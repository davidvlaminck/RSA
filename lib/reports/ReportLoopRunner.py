import json
import logging
import os
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytz

from datasources.arango import SingleArangoConnector
from lib.connectors.Neo4JConnector import SingleNeo4JConnector
from lib.connectors.PostGISConnector import SinglePostGISConnector
from lib.mail.MailContent import MailContent
from lib.mail.MailSender import MailSender
from lib.reports.instantiator import create_report_instance, discover_and_instantiate_reports
from lib.reports.pipeline_runner import run_pipelines_by_datasource
from outputs.sheets_wrapper import SingleSheetsWrapper
from SettingsManager import SettingsManager
from scripts.ops.aggregate_summaries import process_once

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))
BRUSSELS = ZoneInfo("Europe/Brussels")
RETRIES = 5


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

        logging.info = print
        logging.basicConfig(filename='logs.txt',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
        # initialize Sheets wrapper if credentials present; allow missing/empty google_api for
        # offline/Excel-only runs (no-Google mode)
        try:
            creds = None
            if isinstance(self.settings.get('google_api', None), dict):
                creds = self.settings.get('google_api', {}).get('credentials_path')
            SingleSheetsWrapper.init(service_cred_path=creds, readonly_scope=False)
        except Exception:
            # best-effort: continue without Google Sheets initialization (Excel-only will be used)
            pass

        # Initialize Excel writer (best-effort)
        # ensure attribute exists even if excel init fails
        self.excel_output_dir = None
        try:
            # if caller provided override, prefer it
            if self._excel_output_dir_override is not None:
                out_dir = str(Path(self._excel_output_dir_override))
            else:
                out_dir = self.settings.get('output', {}).get('excel', {}).get('output_dir')
                if out_dir is None:
                    out_dir = str(Path(self.settings_path).resolve().parents[0] / 'RSA_OneDrive')

            from outputs.excel_wrapper import SingleExcelWriter
            SingleExcelWriter.init(output_dir=out_dir)
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

        neo4j_settings = self.settings['databases']['Neo4j']
        SingleNeo4JConnector.init(uri=neo4j_settings['uri'], user=neo4j_settings['user'],
                                  password=neo4j_settings['password'], database=neo4j_settings['database'])

        postgis_settings = self.settings['databases']['PostGIS']
        SinglePostGISConnector.init(host=postgis_settings['host'], port=postgis_settings['port'],
                                    user=postgis_settings['user'], password=postgis_settings['password'],
                                    database=postgis_settings['database'])

        # Initialize ArangoDB connection (singleton style)
        arango_settings = self.settings['databases']['ArangoDB']
        SingleArangoConnector.init(
            host=arango_settings['host'],
            port=arango_settings['port'],
            user=arango_settings['user'],
            password=arango_settings['password'],
            database=arango_settings['database']
        )

        self.reports = None

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

    @staticmethod
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
        last_run_date = datetime.now(tz=BRUSSELS).date()

        while True:
            if run_right_away:
                self.run()
                run_right_away = False
                last_run_date = datetime.now(tz=BRUSSELS).date()
                continue

            now = datetime.now(tz=pytz.timezone("Europe/Brussels"))
            if last_run_date == now.date() or not self._is_within_run_window(now):
                logging.info(f'{datetime.now(tz=BRUSSELS)}: not yet the right time to run reports.')
                time.sleep(60)
                continue

            # start running reports now
            self.run()
            last_run_date = datetime.now(tz=BRUSSELS).date()

    def run(self):
        """Run all reports either sequentially or in parallel based on settings."""
        execution_mode = self.settings.get('report_execution', {}).get('mode', 'sequential')

        if execution_mode == 'parallel_by_datasource':
            self._run_parallel_by_datasource()
        else:
            self._run_sequential()

    def run_selected(self, report_names: list[str]):
        """Run a specific list of reports using the configured execution mode."""
        execution_mode = self.settings.get('report_execution', {}).get('mode', 'sequential')

        if execution_mode == 'parallel_by_datasource':
            self._run_parallel_by_datasource(report_names)
        else:
            self._run_sequential(report_names)

    def _run_sequential(self, report_names: list[str] | None = None):
        """Run reports one at a time (original behavior)."""
        # start running reports now and at midnight
        logging.info(f"{datetime.now(tz=BRUSSELS)}: let's run the reports now")

        # detect reports or use the provided list
        if report_names is None:
            report_instances = discover_and_instantiate_reports()
        else:
            report_instances = [
                inst for inst in (create_report_instance(name) for name in report_names) if inst is not None
            ]

        if not report_instances:
            logging.warning("No reports found to execute.")
            return

        # Map instances to their class names for tracking
        reports_to_do = {type(inst).__name__: inst for inst in report_instances}
        reports_run = 0

        while reports_run < RETRIES and reports_to_do:
            reports_run += 1
            for report_name in sorted(reports_to_do.keys()):
                try:
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
                except Exception as ex:
                    logging.info(f"exception happened in report {report_name}: {ex}")
                    logging.exception(ex)
                    logging.error(f'failed completing report {report_name}')
            logging.info(
                f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: done running report loop {reports_run}. '
                f'Reports left to do: {len(reports_to_do)}'
            )

        logging.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: done running the reports')

        self.mail_sender.send_all_mails()
        self.adjust_mailed_info_in_sheets(sender=self.mail_sender)

        logging.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: '
                       f'sent all mails_to_send ({len(list(self.mail_sender.mails_to_send))})')
        # After all reports are done, aggregate staged summary updates.
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
            output_dir = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
            logging.info(f'Running summary aggregator for staged dir {staged_dir}')
            # process_once returns number of processed files
            try:
                processed = process_once(staged_dir, output_dir, limit=1000, dry_run=False)
                logging.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logging.error(f'Failed running aggregate_summaries.process_once: {ex}')
        except Exception as ex:
            logging.error(f'Could not run aggregator: {ex}')

    def _run_parallel_by_datasource(self, report_names: list[str] | None = None):
        """Run reports in parallel, grouped by datasource to avoid DB contention.

        This mode:
        - Groups reports by database type (ArangoDB, PostGIS, Neo4j)
        - Runs one report from each database concurrently
        - Respects memory constraints (max 2-3 concurrent processes)
        - Provides timeout protection for stuck reports
        """
        logging.info(f"{datetime.now(tz=BRUSSELS)}: starting parallel-by-datasource execution")

        # Discover all report names or use provided list
        if report_names is None:
            report_instances = discover_and_instantiate_reports()
            if not report_instances:
                logging.warning("No reports found to execute.")
                return
            report_names = [type(inst).__name__ for inst in report_instances]
        else:
            report_names = list(report_names)

        logging.info(f"Found {len(report_names)} reports to execute")

        # Write settings to temp file for worker processes
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.settings, f)
            settings_path = f.name

        try:
            run_pipelines_by_datasource(
                report_names,
                self.settings,
                settings_path,
                stream_output=True,
            )

        finally:
            # Clean up temp settings file
            try:
                os.unlink(settings_path)
            except Exception:
                pass

        logging.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: parallel execution complete')
        # After parallel pipelines completed, run the aggregator once to apply staged summaries
        try:
            staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
            output_dir = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
            logging.info(f'Running summary aggregator for staged dir {staged_dir} (parallel mode)')
            try:
                processed = process_once(staged_dir, output_dir, limit=1000, dry_run=False)
                logging.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logging.error(f'Failed running aggregate_summaries.process_once: {ex}')
        except Exception as ex:
            logging.error(f'Could not run aggregator after parallel pipelines: {ex}')

    def run_all_no_google(self, output_dir: str | None = None, limit: int = 1000, timeout_seconds: int | None = None, max_concurrent: int | None = None):
        """Run all reports (discovering from Reports/) in no-Google mode.

        This prepares a temporary settings file where Google is disabled and Excel
        output is forced. It then runs pipelines grouped by datasource (parallel)
        and applies staged summary updates via the aggregator.
        """
        # Build a modified settings dict based on existing settings but disable Google
        # and force Excel output for workers by writing a temporary settings file.
        try:
            # load base settings from original settings file if possible
            base_settings = {}
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as fh:
                    base_settings = json.load(fh)
            except Exception:
                base_settings = dict(self.settings or {})

            # Ensure structure
            if 'output' not in base_settings or not isinstance(base_settings['output'], dict):
                base_settings['output'] = {}
            if 'excel' not in base_settings['output'] or not isinstance(base_settings['output']['excel'], dict):
                base_settings['output']['excel'] = {}

            # Determine output directory
            out_dir = output_dir or base_settings['output']['excel'].get('output_dir')
            if out_dir is None:
                repo_root = Path(self.settings_path).resolve().parents[0]
                out_dir = str(repo_root / 'RSA_OneDrive')
            base_settings['output']['excel']['output_dir'] = out_dir

            # Force Excel and disable Google API credentials
            base_settings['force_excel'] = True
            base_settings['google_api'] = {}

            # Inject execution controls if provided (timeout and max concurrency)
            if timeout_seconds is not None or max_concurrent is not None:
                if 'report_execution' not in base_settings or not isinstance(base_settings['report_execution'], dict):
                    base_settings['report_execution'] = {}
                if timeout_seconds is not None:
                    base_settings['report_execution']['timeout_seconds'] = int(timeout_seconds)
                if max_concurrent is not None:
                    base_settings['report_execution']['max_concurrent'] = int(max_concurrent)

            # write temp settings file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmpf:
                json.dump(base_settings, tmpf, indent=2)
                tmp_settings_path = tmpf.name

            # discover report names
            report_instances = discover_and_instantiate_reports()
            report_names = [type(inst).__name__ for inst in report_instances] if report_instances else []

            if not report_names:
                logging.warning('No reports discovered to run in no-Google mode')
                return

            # initialize Excel writer for this process (best-effort)
            try:
                from outputs.excel_wrapper import SingleExcelWriter
                SingleExcelWriter.init(output_dir=out_dir)
                self.excel_output_dir = Path(out_dir)
            except Exception:
                pass

            # run pipelines grouped by datasource using the temp settings file so workers
            # will not try to initialize Google and will prefer Excel output
            try:
                run_pipelines_by_datasource(report_names, base_settings, tmp_settings_path, stream_output=True)
            finally:
                try:
                    os.unlink(tmp_settings_path)
                except Exception:
                    pass

            # apply staged summaries
            try:
                staged_dir = (self.excel_output_dir / 'staged_summaries') if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive') / 'staged_summaries'
                output_dir_path = self.excel_output_dir if hasattr(self, 'excel_output_dir') else Path('RSA_OneDrive')
                logging.info(f'Running summary aggregator for staged dir {staged_dir} (no-Google mode)')
                processed = process_once(staged_dir, output_dir_path, limit=limit, dry_run=False)
                logging.info(f'Aggregate summaries processed {processed} files')
            except Exception as ex:
                logging.error(f'Failed running aggregate_summaries.process_once (no-Google mode): {ex}')

        except Exception as e:
            logging.exception('run_all_no_google failed: %s', e)

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
                        logging.error(f"exception {ex} happened in adjusting mailed info in sheet {sheet_id}")
                        logging.error(traceback.format_exc())
            except Exception as ex:
                logging.error(f"exception happened in adjusting mailed info in sheets: {ex}")
                logging.error(traceback.format_exc())
