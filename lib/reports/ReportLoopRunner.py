import copy
import json
import logging
import os
import sys
import tempfile
import time
import traceback
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Callable

import pytz

from datasources.arango import SingleArangoConnector
from lib.connectors.Neo4JConnector import SingleNeo4JConnector
from lib.connectors.PostGISConnector import SinglePostGISConnector
from lib.mail.MailContent import MailContent
from lib.mail.MailSender import MailSender
from lib.reports.instantiator import create_report_instance, discover_and_instantiate_reports
from lib.reports.parallel_utils import group_reports_by_datasource
from lib.reports.pipeline_runner import (
    run_pipelines_by_datasource,
    _run_worker,
    _read_worker_status,
    _sort_reports_by_duration,
)
from lib.connectors.pipeline_state import PipelineState, enqueue_sqlite_job
from outputs.sheets_wrapper import SingleSheetsWrapper
from SettingsManager import SettingsManager
from scripts.ops.aggregate_summaries import process_once
from outputs.summary_stager import clear_staged_processed

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))
BRUSSELS = ZoneInfo("Europe/Brussels")
RETRIES = 5

logger = logging.getLogger(__name__)


def reinitialize_database_connections(settings: dict, arango_timeout: int = 180) -> None:
    """Re-initialize all database singletons from the current settings.
    
    Args:
        settings: Settings dictionary with database credentials.
        arango_timeout: ArangoDB request timeout in seconds (default 180).
    """
    databases = settings.get('databases', {}) if isinstance(settings, dict) else {}
    
    neo4j_settings = databases.get('Neo4j')
    if neo4j_settings:
        try:
            SingleNeo4JConnector.reset()
        except Exception:
            pass
        try:
            SingleNeo4JConnector.init(uri=neo4j_settings['uri'], user=neo4j_settings['user'],
                                      password=neo4j_settings['password'], database=neo4j_settings['database'])
        except Exception as exc:
            logger.warning(f"Could not reinitialize Neo4J: {exc}")
    else:
        logger.debug("Neo4j settings not configured; skipping reinitialization")

    postgis_settings = databases.get('PostGIS')
    if postgis_settings:
        try:
            SinglePostGISConnector.reset()
        except Exception:
            pass
        try:
            SinglePostGISConnector.init(host=postgis_settings['host'], port=postgis_settings['port'],
                                        user=postgis_settings['user'], password=postgis_settings['password'],
                                        database=postgis_settings['database'])
        except Exception as exc:
            logger.warning(f"Could not reinitialize PostGIS: {exc}")
    else:
        logger.debug("PostGIS settings not configured; skipping reinitialization")

    arango_settings = databases.get('ArangoDB')
    if arango_settings:
        try:
            SingleArangoConnector.reset()
            # expose settings so init() can read query_max_runtime / query_memory_limit
            SingleArangoConnector._arango_settings = arango_settings
            SingleArangoConnector.init(
                host=arango_settings['host'],
                port=arango_settings['port'],
                user=arango_settings['user'],
                password=arango_settings['password'],
                database=arango_settings['database'],
                request_timeout=arango_timeout,
            )
            # Bound server-side query runtime to this attempt's client timeout so a
            # hanging query is aborted on the ArangoDB server itself (not just the client).
            try:
                SingleArangoConnector.set_query_bounds(
                    max_runtime=arango_timeout,
                    memory_limit=arango_settings.get('query_memory_limit'),
                )
            except Exception:
                pass
        except Exception as exc:
            logger.warning(f"Could not reinitialize ArangoDB: {exc}")
    else:
        logger.debug("ArangoDB settings not configured; skipping reinitialization")


class ReportLoopRunner:
    def __init__(self, settings_path, excel_output_dir: str | None = None):
        """Initialize runner.

        Args:
            settings_path: Path to settings JSON used by SettingsManager.
            excel_output_dir: Optional override for Excel output directory. If provided,
                this value takes precedence over settings['output']['excel']['output_dir'].
        """
        self.settings_path = settings_path
        # optional override supplied by caller (e.g., main.py)
        self._excel_output_dir_override = excel_output_dir
        settings_manager = SettingsManager(settings_path=settings_path)
        self.settings = settings_manager.settings

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )
        # Initialize Excel writer and Excel-backed Sheets wrapper (best-effort)
        # ensure attribute exists even if excel init fails
        self.excel_output_dir = None
        try:
            # if caller provided override, prefer it
            if self._excel_output_dir_override is not None:
                out_dir = str(Path(self._excel_output_dir_override))
            else:
                drive_cfg = self.settings.get('drive_sync', {}) if isinstance(self.settings, dict) else {}
                excel_cfg = self.settings.get('output', {}).get('excel', {}) if isinstance(self.settings, dict) else {}
                out_dir = drive_cfg.get('local_folder') or excel_cfg.get('output_dir')
                if out_dir is None:
                    out_dir = str(Path(self.settings_path).resolve().parents[0] / 'RSA_OneDrive')

            from outputs.excel_wrapper import SingleExcelWriter
            from outputs.sheets_wrapper import SingleSheetsWrapper
            SingleExcelWriter.init(output_dir=out_dir)
            SingleSheetsWrapper.init(output_dir=out_dir)
            # remember excel output dir for aggregator usage
            self.excel_output_dir = Path(out_dir)
            # also update settings so worker processes reading settings will see the path
            try:
                if isinstance(self.settings, dict):
                    self.settings.setdefault('output', {})
                    self.settings['output'].setdefault('excel', {})
                    self.settings['output']['excel']['output_dir'] = out_dir
            except Exception:
                # non-fatal if we can't mutate settings
                pass
        except Exception:
            # best-effort: continue without Excel initialization
            pass

        reinitialize_database_connections(self.settings)

        self.reports = None
        pipeline_state_cfg = self.settings.get("pipeline_state", {}) if isinstance(self.settings, dict) else {}
        self.pipeline_status = None
        self._pipeline_state_db_path = None
        if pipeline_state_cfg.get("enabled", True):
            db_path = pipeline_state_cfg.get("db_path", "")
            if db_path:
                self.pipeline_status = PipelineState(db_path)
                self._pipeline_state_db_path = db_path

        # Optional callback invoked before starting a daily run.
        # Should return True when preconditions are met; False to retry later.
        self.on_before_run: Callable[[datetime], bool] | None = None

        # Optionele callback die aangeroepen wordt na elke volledige run.
        # Gebruik in main.py om bv. bestanden naar Google Drive te uploaden.
        # Voorbeeld: runner.on_run_complete = lambda: upload_folder_to_drive(...)
        self.on_run_complete: callable | None = None

        self.dir_path = os.path.abspath(os.path.join(os.sep, ROOT_DIR, 'Reports'))
        self.mail_sender = MailSender(mail_settings=self.settings['smtp_options'])
        self.output_type = (self.settings.get('output', {}) or {}).get('type', 'GoogleSheets')
        self.output_settings = (self.settings.get('output', {}) or {})

    @staticmethod
    def _parse_hms_to_seconds(hms: str) -> int:
        """Parse HH:MM:SS into seconds since midnight."""
        parts = (hms or "").split(":")
        if len(parts) != 3:
            raise ValueError(f"Invalid time format '{hms}', expected HH:MM:SS")
        h, m, s = (int(p) for p in parts)
        if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
            raise ValueError(f"Invalid time value '{hms}', expected HH:MM:SS within normal ranges")
        return h * 3600 + m * 60 + s

    def _get_run_window(self) -> tuple[int, int]:
        """Return (start_seconds, end_seconds) from settings."""
        time_cfg = self.settings.get('time', {}) if isinstance(self.settings, dict) else {}
        start_hms = time_cfg.get('start', '05:00:00')
        end_hms = time_cfg.get('end', '23:59:59')
        return self._parse_hms_to_seconds(start_hms), self._parse_hms_to_seconds(end_hms)

    def _is_within_run_window(self, now: datetime) -> bool:
        start_s, end_s = self._get_run_window()
        now_s = now.hour * 3600 + now.minute * 60 + now.second
        if start_s <= end_s:
            return start_s <= now_s <= end_s
        return now_s >= start_s or now_s <= end_s


    def _clean_report_headers(report_rows):
        """Utility: remove duplicate header row if the first two rows are identical.

        Kept as a staticmethod to avoid nesting functions inside `run()`.
        """
        if not report_rows:
            return report_rows
        # If the first two rows are identical, remove the second
        if len(report_rows) > 1 and report_rows[0] == report_rows[1]:
            return [report_rows[0]] + report_rows[2:]
        return report_rows

    def start(self, run_right_away: bool):
        last_run_date = None

        while True:
            now = datetime.now(tz=BRUSSELS)

            if run_right_away:
                # Respect the same pre-run hook for immediate execution.
                if self.on_before_run is not None:
                    while True:
                        now = datetime.now(tz=BRUSSELS)
                        try:
                            if self.on_before_run(now):
                                break
                        except Exception as exc:
                            logger.error(f"on_before_run callback mislukt: {exc}")
                        logger.info(f"{datetime.now(tz=BRUSSELS)}: waiting for pre-run conditions")
                        time.sleep(60)
                if self.pipeline_status is not None:
                    now = datetime.now(tz=BRUSSELS)
                    if not self._wait_for_preconditions(now):
                        run_right_away = False
                        last_run_date = now.date()
                        continue
                self.run()
                run_right_away = False
                last_run_date = datetime.now(tz=BRUSSELS).date()
                continue

            now = datetime.now(tz=BRUSSELS)

            # Allow external pre-run prerequisites (e.g. daily Drive download sync).
            if self.on_before_run is not None and last_run_date != now.date():
                try:
                    if not self.on_before_run(now):
                        logger.info(f'{datetime.now(tz=BRUSSELS)}: pre-run conditions not yet met.')
                        time.sleep(60)
                        continue
                except Exception as exc:
                    logger.error(f"on_before_run callback mislukt: {exc}")
                    time.sleep(60)
                    continue

            # Signal-based mode: pipeline_state controls when to run, no time window.
            # Backward-compatible mode (no pipeline_state): once-per-day + time window.
            if self.pipeline_status is not None:
                if last_run_date == now.date():
                    logger.info(f'{datetime.now(tz=BRUSSELS)}: already ran today, sleeping until tomorrow.')
                    time.sleep(60)
                    continue
                if not self._wait_for_preconditions(now):
                    last_run_date = now.date()
                    now_seconds = now.hour * 3600 + now.minute * 60 + now.second
                    sleep_seconds = 86400 - now_seconds
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
                    continue
            elif last_run_date == now.date() or not self._is_within_run_window(now):
                logger.info(f'{datetime.now(tz=BRUSSELS)}: not yet the right time to run reports.')
                time.sleep(60)
                continue

            # start running reports now
            self.run()
            last_run_date = datetime.now(tz=BRUSSELS).date()

    def _wait_for_preconditions(self, now: datetime) -> bool:
        """Wait until pipeline preconditions are met.

        Passive wait until 4am, then active wait up to 3 hours for postgis_sync signal.
        Returns True when ready, False if timeout expired (reports aborted).
        """
        passive_until_hms = self.settings.get('pipeline_state', {}).get('passive_wait_until', '04:00:00')
        active_timeout = self.settings.get('pipeline_state', {}).get('postgis_wait_timeout_seconds', 10800)

        passive_until_seconds = self._parse_hms_to_seconds(passive_until_hms)
        now_seconds = now.hour * 3600 + now.minute * 60 + now.second

        if now_seconds < passive_until_seconds:
            sleep_seconds = passive_until_seconds - now_seconds
            logger.info(f"{now}: passive wait until {passive_until_hms} ({sleep_seconds}s)")
            time.sleep(sleep_seconds)
            now_seconds = passive_until_seconds

        deadline = time.time() + active_timeout
        while time.time() < deadline:
            current = self.pipeline_status.get()
            if current:
                phase = current.get('phase', '')
                status = current.get('status', '')
                if phase in ('postgis_sync_paused', 'postgis_sync_running', 'postgis_sync_resuming'):
                    return True
                if phase == 'rsa_queries' and status not in ('completed', 'time-out', 'aborted', 'failed'):
                    return True
            time.sleep(60)

        if self.pipeline_status is not None:
            enqueue_sqlite_job("update_pipeline_state", {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "phase": "rsa_queries",
                "status": "aborted",
                "message": f"Timeout waiting for postgis_sync after {active_timeout}s"
            })
        logger.warning(f'{datetime.now(tz=BRUSSELS)}: postgis_sync preconditions not met within {active_timeout}s; rsa_queries aborted.')
        return False

    def _update_pipeline_message(self, message: str, phase: str = "rsa_queries", status: str = "running") -> None:
        if self.pipeline_status is not None:
            try:
                enqueue_sqlite_job("update_pipeline_state", {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "phase": phase,
                    "status": status,
                    "message": message
                })
            except Exception:
                pass

    def _should_run_rsa_queries(self) -> bool:
        """Check SQLite pipeline_state to determine if RSA queries should run.

        Returns True if the pipeline is in a state where RSA queries should execute:
        - phase is postgis_sync_paused, postgis_sync_running, or postgis_sync_resuming
        - phase is rsa_queries (not yet completed/time-out)

        Returns False if the pipeline is idle, in an earlier phase, or rsa_queries
        has already finished (e.g. after a midnight reset or crash recovery).
        """
        if self.pipeline_status is None:
            return True

        current = self.pipeline_status.get()
        if current is None:
            return True

        phase = current.get('phase', '')
        status = current.get('status', '')

        if phase == 'idle':
            logger.info(
                f'{datetime.now(tz=BRUSSELS)}: pipeline is idle (midnight reset), '
                f'not running rsa_queries.'
            )
            return False

        if phase == 'rsa_queries' and status in ('completed', 'time-out', 'aborted', 'failed'):
            logger.info(
                f'{datetime.now(tz=BRUSSELS)}: rsa_queries already {status}, '
                f'not running again.'
            )
            return False

        if phase in ('postgis_sync_paused', 'postgis_sync_running', 'postgis_sync_resuming'):
            return True

        if phase == 'rsa_queries':
            return True

        logger.info(
            f'{datetime.now(tz=BRUSSELS)}: pipeline phase is {phase} ({status}), '
            f'rsa_queries should not run yet.'
        )
        return False

    def _check_pipeline_still_valid(self) -> bool:
        """Check during report execution whether the pipeline is still in a valid state.

        Returns False if the pipeline has been reset (e.g. back to idle) and RSA
        queries should stop immediately.
        """
        if self.pipeline_status is None:
            return True

        current = self.pipeline_status.get()
        if current is None:
            return True

        phase = current.get('phase', '')
        status = current.get('status', '')

        if phase == 'idle':
            logger.warning(
                f'{datetime.now(tz=BRUSSELS)}: pipeline reset to idle during rsa_queries, '
                f'aborting report execution.'
            )
            return False

        if phase == 'rsa_queries' and status in ('completed', 'time-out', 'aborted', 'failed'):
            logger.warning(
                f'{datetime.now(tz=BRUSSELS)}: rsa_queries already {status} (external), '
                f'aborting report execution.'
            )
            return False

        return True

    def _preflight_checks(self) -> None:
        """Verify database connectivity before starting a report run.

        Fails fast if PostGIS is unreachable, preventing hours of wasted runtime
        on a dead datasource.
        """
        try:
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            connector = SinglePostGISConnector.get_connector()
            conn = connector.pool.getconn()
            try:
                conn.cursor().execute("SELECT 1")
            finally:
                connector.pool.putconn(conn)
            logger.info("Preflight check: PostGIS connection OK")
        except Exception as exc:
            logger.error(f"Preflight check: PostGIS connection failed: {exc}")
            if self.pipeline_status is not None:
                enqueue_sqlite_job("update_pipeline_state", {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "phase": "rsa_queries",
                    "status": "failed",
                    "message": f"Preflight check failed: PostGIS unreachable: {exc}",
                })
            raise RuntimeError(f"PostGIS preflight check failed: {exc}") from exc

    def run(self):
        """Run all reports either sequentially or in parallel based on settings.

        Implements the 3-hour timeout from the pipeline spec: if reports are still
        running after the configured timeout, report execution stops but the summary
        assembly always runs. The pipeline state is then set to ``time-out`` (not
        ``failed``) so the orchestrator can proceed to PostGIS resume + drive_upload.
        """
        if not self._should_run_rsa_queries():
            logger.info(f'{datetime.now(tz=BRUSSELS)}: skipping rsa_queries, pipeline not in valid state.')
            return

        self._preflight_checks()

        if self.pipeline_status is not None:
            enqueue_sqlite_job("update_pipeline_state", {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "phase": "rsa_queries",
                "status": "running",
                "message": "RSA queries gestart"
            })

        timeout_seconds = self.settings.get('pipeline_state', {}).get('rsa_queries_timeout_seconds', 10800)
        deadline = time.time() + timeout_seconds
        timed_out = False

        try:
            execution_mode = self.settings.get('report_execution', {}).get('mode', 'sequential')

            if execution_mode == 'parallel_by_datasource':
                timed_out = self._run_parallel_by_datasource(deadline=deadline)
            else:
                timed_out = self._run_sequential(deadline=deadline)

            if self.pipeline_status is not None:
                if timed_out:
                    enqueue_sqlite_job("update_pipeline_state", {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "phase": "rsa_queries",
                        "status": "time-out",
                        "message": f"RSA queries time-out na {timeout_seconds}s; overzicht samengesteld"
                    })
                else:
                    enqueue_sqlite_job("update_pipeline_state", {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "phase": "rsa_queries",
                        "status": "completed",
                        "message": "RSA queries voltooid"
                    })
        except Exception as exc:
            if self.pipeline_status is not None:
                enqueue_sqlite_job("update_pipeline_state", {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "phase": "rsa_queries",
                    "status": "failed",
                    "message": str(exc)
                })
            raise

        if self.on_run_complete is not None:
            try:
                self.on_run_complete()
            except Exception as exc:
                logger.error(f"on_run_complete callback mislukt: {exc}")

    def run_selected(self, report_names: list[str]):
        """Run a specific list of reports using the configured execution mode."""
        execution_mode = self.settings.get('report_execution', {}).get('mode', 'sequential')

        if execution_mode == 'parallel_by_datasource':
            self._run_parallel_by_datasource(report_names)
        else:
            self._run_sequential(report_names)

    def _run_sequential(self, report_names: list[str] | None = None, deadline: float | None = None):
        """Run reports one at a time (original behavior).

        Args:
            report_names: Optional list of specific reports to run.
            deadline: Optional unix timestamp. When reached, report execution stops
                but the summary aggregation still runs.
        Returns:
            True if the deadline was exceeded, False otherwise.
        """
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if self.excel_output_dir else Path('RSA_OneDrive') / 'staged_summaries'
            clear_staged_processed(staged_dir)
        except Exception:
            logger.exception('Failed to clear staged_summaries/processed before sequential run')

        # start running reports now and at midnight
        logger.info(f"{datetime.now(tz=BRUSSELS)}: let's run the reports now")

        # detect reports or use the provided list
        if report_names is None:
            report_instances = discover_and_instantiate_reports()
        else:
            report_instances = [
                inst for inst in (create_report_instance(name) for name in report_names) if inst is not None
            ]

        if not report_instances:
            logger.warning("No reports found to execute.")
            return False

        # Map instances to their class names for tracking
        reports_to_do = {type(inst).__name__: inst for inst in report_instances}
        reports_run = 0
        timed_out = False

        while reports_run < RETRIES and reports_to_do:
            if deadline is not None and time.time() >= deadline:
                timed_out = True
                logger.warning(
                    f'{datetime.now(tz=BRUSSELS)}: rsa_queries deadline reached, '
                    f'stopping report execution ({len(reports_to_do)} reports remaining)'
                )
                break
            reports_run += 1
            if reports_run > 1:
                # Calculate timeout for this retry (60s, 120s, 180s, etc.)
                retry_timeout = 60 * reports_run
                reinitialize_database_connections(self.settings, arango_timeout=retry_timeout)
            total = len(reports_to_do)
            for idx, report_name in enumerate(sorted(reports_to_do.keys()), 1):
                if deadline is not None and time.time() >= deadline:
                    timed_out = True
                    logger.warning(
                        f'{datetime.now(tz=BRUSSELS)}: rsa_queries deadline reached during {report_name}, '
                        f'stopping report execution ({len(reports_to_do)} reports remaining)'
                    )
                    break
                if not self._check_pipeline_still_valid():
                    timed_out = True
                    logger.warning(
                        f'{datetime.now(tz=BRUSSELS)}: pipeline state changed during {report_name}, '
                        f'stopping report execution ({len(reports_to_do)} reports remaining)'
                    )
                    break
                try:
                    self._update_pipeline_message(f"Verwerken: {report_name} ({idx}/{total})", "rsa_queries", "running")
                    report_instance = reports_to_do[report_name]
                    report_instance.init_report()
                    # set pipeline-wide defaults (reports can override)
                    if hasattr(report_instance, 'report') and report_instance.report is not None:
                        if hasattr(report_instance.report, 'output'):
                            report_instance.report.output = self.output_type
                        if hasattr(report_instance.report, 'output_settings'):
                            report_instance.report.output_settings = self.output_settings
                    report_instance.run_report(sender=self.mail_sender)
                    # Clean up duplicate headers in the report output if possible
                    if hasattr(report_instance.report, 'rows'):
                        report_instance.report.rows = self._clean_report_headers(report_instance.report.rows)
                    del reports_to_do[report_name]
                    logger.info(f"✅ Report {report_name} completed successfully")
                except Exception as ex:
                    logger.info(f"exception happened in report {report_name}: {ex}")
                    logger.exception(ex)
                    logger.error(f'❌ Report {report_name} failed — re-added to retry queue')
            logger.info(
                f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: done running report loop {reports_run}. '
                f'Reports left to do: {len(reports_to_do)}'
            )

        logger.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: done running the reports')

        self.mail_sender.send_all_mails()
        self.adjust_mailed_info_in_sheets(sender=self.mail_sender)

        logger.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: '
                       f'sent all mails_to_send ({len(list(self.mail_sender.mails_to_send))})')
        # After all reports are done, aggregate staged summary updates.
        # This ALWAYS runs, even on timeout, so the overview can be assembled.
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
            output_dir = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
            logger.info(f'Running summary aggregator for staged dir {staged_dir}')
            # process_once returns number of processed files
            try:
                processed = process_once(staged_dir, output_dir, limit=1000, dry_run=False)
                logger.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logger.error(f'Failed running aggregate_summaries.process_once: {ex}')
        except Exception as ex:
            logger.error(f'Could not run aggregator: {ex}')

        return timed_out

    def _run_datasource_worker(self, datasource: str, report_names: list[str], query_timeout: int,
                                batch_size: int, batch_timeout: float, deadline: float,
                                process_timeout: float = 0) -> list[str]:
        """Run reports for a single datasource in a worker subprocess.

        Returns list of failed report names (empty list on success).
        """
        worker_settings = copy.deepcopy(self.settings)
        worker_settings['query_timeout_seconds'] = query_timeout
        worker_settings['arango_request_timeout'] = query_timeout

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(worker_settings, f)
            settings_path = f.name

        status_fd, status_file = tempfile.mkstemp(suffix='.jsonl', prefix='worker_status_')
        os.close(status_fd)

        try:
            result = _run_worker(
                report_names,
                settings_path,
                stream_output=True,
                status_file=status_file,
                batch_size=batch_size,
                batch_timeout=batch_timeout,
                deadline=deadline,
                process_timeout=process_timeout,
            )
            actual_failed = _read_worker_status(status_file, report_names)
            if actual_failed is None:
                actual_failed = report_names if result.get("status") != "success" else []
            return actual_failed
        finally:
            try:
                os.unlink(settings_path)
            except Exception:
                pass
            try:
                os.unlink(status_file)
            except Exception:
                pass

    def _run_parallel_by_datasource(self, report_names: list[str] | None = None, deadline: float | None = None):
        """Run reports in parallel, grouped by datasource to avoid DB contention.

        This mode:
        - Groups reports by database type (ArangoDB, PostGIS, Neo4j)
        - Runs one report from each database concurrently
        - Respects memory constraints (max 2-3 concurrent processes)
        - Provides per-report query timeout protection (configurable)
        - Retries failed/timed out reports with increasing query timeout (+60s per attempt)
        - Per-datasource retry: failed datasources are retried independently
        - Batch execution: reports are split into batches of 10 with per-batch timeout
        - Deadline awareness: workers stop when deadline is reached

        Args:
            report_names: Optional list of specific reports to run.
            deadline: Optional unix timestamp. When reached, report execution stops
                but the summary aggregation still runs.
        Returns:
            True if the deadline was exceeded, False otherwise.
        """
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if self.excel_output_dir else Path('RSA_OneDrive') / 'staged_summaries'
            clear_staged_processed(staged_dir)
        except Exception:
            logger.exception('Failed to clear staged_summaries/processed before parallel run')

        logger.info(f"{datetime.now(tz=BRUSSELS)}: starting parallel-by-datasource execution")

        if report_names is None:
            report_instances = discover_and_instantiate_reports()
            if not report_instances:
                logger.warning("No reports found to execute.")
                return False
            report_names = [type(inst).__name__ for inst in report_instances]
        else:
            report_names = list(report_names)

        logger.info(f"Found {len(report_names)} reports to execute")

        exec_cfg = self.settings.get("report_execution", {}) if isinstance(self.settings, dict) else {}
        # Honor both keys: prefer query_timeout_seconds, fall back to the documented timeout_seconds.
        base_query_timeout = exec_cfg.get("query_timeout_seconds") or exec_cfg.get("timeout_seconds", 60)
        max_workers = min(exec_cfg.get("max_concurrent", 2), 3)

        batch_size = 10
        if deadline and time.time() < deadline:
            remaining = deadline - time.time()
            batch_timeout = max(60, remaining / 10)
            # Hard backstop per datasource worker, derived from the remaining deadline budget.
            overall_timeout = remaining / 2
        else:
            batch_timeout = 0
            overall_timeout = 0

        groups = group_reports_by_datasource(report_names)
        pipelines = {ds: items for ds, items in groups.items() if items}
        if not pipelines:
            logger.info("No reports to run in parallel.")
            return False

        drive_cfg = self.settings.get("drive_sync", {})
        excel_cfg = self.settings.get("output", {}).get("excel", {})
        output_dir = Path(drive_cfg.get("local_folder") or excel_cfg.get("output_dir") or "RSA_OneDrive")

        for datasource, report_list in pipelines.items():
            pipelines[datasource] = _sort_reports_by_duration(report_list, output_dir)
            logger.info("Sorted pipeline [%s] by estimated duration: %s", datasource, pipelines[datasource])

        logger.info("Running %d pipelines in parallel (max_workers=%d)", len(pipelines), max_workers)

        timed_out = False
        remaining = {ds: list(reports) for ds, reports in pipelines.items()}
        datasource_attempts = {ds: 0 for ds in remaining}

        while any(remaining.values()):
            if all(datasource_attempts[ds] >= RETRIES for ds in remaining if remaining[ds]):
                break

            if deadline and time.time() >= deadline:
                timed_out = True
                logger.warning(
                    f'{datetime.now(tz=BRUSSELS)}: rsa_queries deadline reached, '
                    f'stopping parallel execution ({sum(len(v) for v in remaining.values())} reports remaining)'
                )
                break

            active = {ds: reports for ds, reports in remaining.items() if reports and datasource_attempts[ds] < RETRIES}
            if not active:
                break

            max_workers_now = min(max_workers, len(active))

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_now) as executor:
                future_to_ds = {}
                for ds, reports in active.items():
                    datasource_attempts[ds] += 1
                    attempt = datasource_attempts[ds]
                    current_query_timeout = base_query_timeout + (60 * (attempt - 1))

                    if attempt > 1:
                        reinitialize_database_connections(self.settings, arango_timeout=current_query_timeout)

                    logger.info(
                        f"Starting [%s] attempt %d/%d with query_timeout=%ds for %d reports",
                        ds, attempt, RETRIES, current_query_timeout, len(reports)
                    )
                    self._update_pipeline_message(
                        f"Parallel: {len(reports)} rapporten voor {ds}, poging {attempt}/{RETRIES}",
                        "rsa_queries", "running"
                    )

                    future = executor.submit(
                        self._run_datasource_worker,
                        ds, reports, current_query_timeout, batch_size, batch_timeout, deadline,
                        overall_timeout,
                    )
                    future_to_ds[future] = ds

                while future_to_ds:
                    done, _ = concurrent.futures.wait(
                        future_to_ds,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for future in done:
                        ds = future_to_ds.pop(future)
                        try:
                            failed = future.result(timeout=1)
                        except concurrent.futures.TimeoutError:
                            failed = remaining[ds]
                            logger.error("[%s] worker result timed out", ds)
                        except Exception as exc:
                            failed = remaining[ds]
                            logger.error("[%s] worker error: %s", ds, exc)

                        remaining[ds] = failed

                        if failed and datasource_attempts[ds] < RETRIES:
                            if deadline and time.time() >= deadline:
                                timed_out = True
                                logger.warning(
                                    "Deadline reached, not retrying %s (%d reports)",
                                    ds, len(failed)
                                )
                                continue
                            datasource_attempts[ds] += 1
                            attempt = datasource_attempts[ds]
                            current_query_timeout = base_query_timeout + (60 * (attempt - 1))
                            reinitialize_database_connections(self.settings, arango_timeout=current_query_timeout)
                            logger.warning(
                                "❌ [%s] attempt %d failed for %d reports, starting immediate retry %d/%d with query_timeout=%ds",
                                ds, attempt - 1, len(failed), attempt, RETRIES, current_query_timeout
                            )
                            retry_future = executor.submit(
                                self._run_datasource_worker,
                                ds, failed, current_query_timeout, batch_size, batch_timeout, deadline,
                                overall_timeout,
                            )
                            future_to_ds[retry_future] = ds
                        elif not failed:
                            logger.info("✅ [%s] completed successfully", ds)

        all_failed = [r for reports in remaining.values() for r in reports]
        if all_failed:
            logger.error(
                f'{datetime.now(tz=BRUSSELS)}: one or more datasource pipelines had failures: {all_failed}'
            )

        logger.info(f'{datetime.now(tz=BRUSSELS)}: parallel execution complete')
        # After parallel pipelines completed, run the aggregator once to apply staged summaries
        # This ALWAYS runs, even on timeout, so the overview can be assembled.
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
            output_dir = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
            logger.info(f'Running summary aggregator for staged dir {staged_dir} (parallel mode)')
            try:
                processed = process_once(staged_dir, output_dir, limit=1000, dry_run=False)
                logger.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logger.error(f'Failed running aggregate_summaries.process_once: {ex}')
        except Exception as ex:
            logger.error(f'Could not run aggregator after parallel pipelines: {ex}')

        return timed_out

    def run_all_no_google(self, output_dir: str | None = None, limit: int = 1000, timeout_seconds: int | None = None, max_concurrent: int | None = None):
        """Run all reports (discovering from Reports/) in no-Google mode.

        This prepares a temporary settings file where Google is disabled and Excel
        output is forced. It then runs pipelines grouped by datasource (parallel)
        and applies staged summary updates via the aggregator.
        """
        try:
            base_settings = {}
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as fh:
                    base_settings = json.load(fh)
            except Exception:
                base_settings = dict(self.settings or {})

            if 'output' not in base_settings or not isinstance(base_settings['output'], dict):
                base_settings['output'] = {}
            if 'excel' not in base_settings['output'] or not isinstance(base_settings['output']['excel'], dict):
                base_settings['output']['excel'] = {}

            drive_cfg = base_settings.get('drive_sync', {}) if isinstance(base_settings, dict) else {}
            excel_cfg = base_settings.get('output', {}).get('excel', {}) if isinstance(base_settings, dict) else {}
            out_dir = output_dir or drive_cfg.get('local_folder') or excel_cfg.get('output_dir')
            if out_dir is None:
                repo_root = Path(self.settings_path).resolve().parents[0]
                out_dir = str(repo_root / 'RSA_OneDrive')
            base_settings['output']['excel']['output_dir'] = out_dir

            base_settings['force_excel'] = True
            base_settings['google_api'] = {}

            if timeout_seconds is not None or max_concurrent is not None:
                if 'report_execution' not in base_settings or not isinstance(base_settings['report_execution'], dict):
                    base_settings['report_execution'] = {}
                if timeout_seconds is not None:
                    base_settings['report_execution']['query_timeout_seconds'] = int(timeout_seconds)
                if max_concurrent is not None:
                    base_settings['report_execution']['max_concurrent'] = int(max_concurrent)

            report_instances = discover_and_instantiate_reports()
            report_names = [type(inst).__name__ for inst in report_instances] if report_instances else []

            if not report_names:
                logger.warning('No reports discovered to run in no-Google mode')
                return

            try:
                from outputs.excel_wrapper import SingleExcelWriter
                SingleExcelWriter.init(output_dir=out_dir)
                self.excel_output_dir = Path(out_dir)
            except Exception:
                pass

            exec_cfg = base_settings.get("report_execution", {}) if isinstance(base_settings, dict) else {}
            base_query_timeout = exec_cfg.get("query_timeout_seconds", 60)
            base_arango_request_timeout = exec_cfg.get("arango_request_timeout_seconds", 180)

            parallel_run = 0
            reports_to_do = list(report_names)

            while parallel_run < RETRIES and reports_to_do:
                parallel_run += 1
                current_query_timeout = base_query_timeout + (60 * (parallel_run - 1))
                current_arango_request_timeout = current_query_timeout

                if parallel_run > 1:
                    reinitialize_database_connections(base_settings, arango_timeout=current_arango_request_timeout)

                base_settings['query_timeout_seconds'] = current_query_timeout
                base_settings['arango_request_timeout'] = current_arango_request_timeout

                logger.info(
                    f'no-Google parallel run attempt {parallel_run} '
                    f'with query_timeout={current_query_timeout}s '
                    f'for {len(reports_to_do)} reports'
                )

                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmpf:
                    json.dump(base_settings, tmpf, indent=2)
                    attempt_settings_path = tmpf.name

                try:
                    return_code, failed_reports = run_pipelines_by_datasource(
                        reports_to_do, base_settings, attempt_settings_path, stream_output=True,
                        batch_size=10,
                    )
                    reports_to_do = failed_reports
                finally:
                    try:
                        os.unlink(attempt_settings_path)
                    except Exception:
                        pass

                logger.info(
                    f'done running no-Google parallel loop {parallel_run}. '
                    f'Reports left to do: {len(reports_to_do)}'
                )

            try:
                staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
                output_dir_path = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
                logger.info(f'Running summary aggregator for staged dir {staged_dir} (no-Google mode)')
                processed = process_once(staged_dir, output_dir_path, limit=limit, dry_run=False)
                logger.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logger.error(f'Failed running aggregate_summaries.process_once (no-Google mode): {ex}')

        except Exception as e:
            logger.exception('run_all_no_google failed: %s', e)

    @staticmethod
    def adjust_mailed_info_in_sheets(sender: MailSender):
        # Normalize possibly lazy/iterable mail containers into lists to satisfy static checkers
        sent_mails = list(sender.sent_mails)
        sheet_info = sender.sheet_info
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        # loop through sent_mails
        # if item is in sheet_info, adjust cell

        for mail_content in sent_mails:
            try:
                if not isinstance(mail_content, MailContent):
                    continue
                sheet_id = mail_content.spreadsheet_id
                if sheet_id not in sheet_info:
                    continue
                found_infos = list(filter(lambda info: info['mail'] == mail_content.receiver and info[
                    'frequency'] == mail_content.frequency, sheet_info[sheet_id]))
                for found_info in found_infos:
                    try:
                        sheets_wrapper.write_data_to_sheet(spreadsheet_id=sheet_id, start_cell=found_info['cell'],
                                                           sheet_name='Overzicht',
                                                           data=[[mail_content.mail_sent.strftime("%Y-%m-%d %H:%M:%S")]])
                    except Exception as ex:
                        logger.error(f"exception {ex} happened in adjusting mailed info in sheet {sheet_id}")
                        logger.error(traceback.format_exc())
            except Exception as ex:
                logger.error(f"exception happened in adjusting mailed info in sheets: {ex}")
                logger.error(traceback.format_exc())
            except Exception as ex:
                logger.error(f"exception happened in adjusting mailed info in sheets: {ex}")
                logger.error(traceback.format_exc())

