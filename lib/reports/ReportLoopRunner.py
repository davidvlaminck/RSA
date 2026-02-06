import logging
import os
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

import pytz

from lib.mail.MailContent import MailContent
from lib.mail.MailSender import MailSender
from lib.connectors.Neo4JConnector import SingleNeo4JConnector
from lib.connectors.PostGISConnector import SinglePostGISConnector
from SettingsManager import SettingsManager
from outputs.sheets_wrapper import SingleSheetsWrapper

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))
BRUSSELS = ZoneInfo("Europe/Brussels")
RETRIES = 5


class ReportLoopRunner:
    def __init__(self, settings_path):
        settings_manager = SettingsManager(settings_path=settings_path)
        self.settings = settings_manager.settings

        logging.info = print
        logging.basicConfig(filename='logs.txt',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
        SingleSheetsWrapper.init(service_cred_path=self.settings['google_api']['credentials_path'],
                                 readonly_scope=False)

        neo4j_settings = self.settings['databases']['Neo4j']
        SingleNeo4JConnector.init(uri=neo4j_settings['uri'], user=neo4j_settings['user'],
                                  password=neo4j_settings['password'], database=neo4j_settings['database'])

        postgis_settings = self.settings['databases']['PostGIS']
        SinglePostGISConnector.init(host=postgis_settings['host'], port=postgis_settings['port'],
                                    user=postgis_settings['user'], password=postgis_settings['password'],
                                    database=postgis_settings['database'])

        # Initialize ArangoDB connection (singleton style)
        arango_settings = self.settings['databases']['ArangoDB']
        from datasources.arango import SingleArangoConnector
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

    def _run_sequential(self):
        """Run reports one at a time (original behavior)."""
        # start running reports now and at midnight
        logging.info(f"{datetime.now(tz=BRUSSELS)}: let's run the reports now")

        # detect reports in Reports package using the shared discovery helper
        from lib.reports.instantiator import discover_and_instantiate_reports
        report_instances = discover_and_instantiate_reports()

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

    def _run_parallel_by_datasource(self):
        """Run reports in parallel, grouped by datasource to avoid DB contention.

        This mode:
        - Groups reports by database type (ArangoDB, PostGIS, Neo4j)
        - Runs one report from each database concurrently
        - Respects memory constraints (max 2-3 concurrent processes)
        - Provides timeout protection for stuck reports
        """
        import subprocess
        import json
        import tempfile
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from lib.reports.parallel_utils import group_reports_by_datasource, create_balanced_batches

        logging.info(f"{datetime.now(tz=BRUSSELS)}: starting parallel-by-datasource execution")

        # Get configuration
        execution_config = self.settings.get('report_execution', {})
        max_concurrent = execution_config.get('max_concurrent', 2)
        timeout_seconds = execution_config.get('timeout_seconds', 1800)  # 30 min default

        # Discover all reports
        from lib.reports.instantiator import discover_and_instantiate_reports
        report_instances = discover_and_instantiate_reports()

        if not report_instances:
            logging.warning("No reports found to execute.")
            return

        # Get report names
        all_report_names = [type(inst).__name__ for inst in report_instances]
        logging.info(f"Found {len(all_report_names)} reports to execute")

        # Group reports by datasource
        report_groups = group_reports_by_datasource(all_report_names)

        # Create balanced batches for parallel execution
        batches = create_balanced_batches(report_groups, max_concurrent=max_concurrent)

        # Write settings to temp file for worker processes
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.settings, f)
            settings_path = f.name

        try:
            # Track results
            successful_reports = []
            failed_reports = []
            timed_out_reports = []

            # Process each batch
            for batch_idx, batch in enumerate(batches, 1):
                logging.info(f"\n{'='*60}")
                logging.info(f"Processing batch {batch_idx}/{len(batches)} ({len(batch)} reports)")
                logging.info(f"{'='*60}")

                # Run reports in this batch concurrently using ThreadPoolExecutor
                # (threads are used to wait for subprocesses, not to run Python code)
                with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                    # Submit all reports in batch
                    future_to_report = {}
                    for datasource, report_name in batch:
                        future = executor.submit(
                            self._run_report_subprocess,
                            report_name,
                            settings_path,
                            timeout_seconds
                        )
                        future_to_report[future] = (datasource, report_name)

                    # Wait for all reports in batch to complete
                    for future in as_completed(future_to_report):
                        datasource, report_name = future_to_report[future]
                        try:
                            result = future.result()
                            if result['status'] == 'success':
                                logging.info(f"✓ [{datasource}] {report_name} completed")
                                successful_reports.append(report_name)
                            elif result['status'] == 'timeout':
                                logging.error(f"⏱ [{datasource}] {report_name} TIMED OUT after {timeout_seconds}s")
                                timed_out_reports.append(report_name)
                            else:
                                logging.error(f"✗ [{datasource}] {report_name} FAILED: {result.get('error', 'Unknown')}")
                                failed_reports.append(report_name)
                        except Exception as e:
                            logging.error(f"✗ [{datasource}] {report_name} EXCEPTION: {e}")
                            failed_reports.append(report_name)

            # Print summary
            logging.info(f"\n{'='*60}")
            logging.info("EXECUTION SUMMARY")
            logging.info(f"{'='*60}")
            logging.info(f"✓ Successful: {len(successful_reports)}/{len(all_report_names)}")
            if failed_reports:
                logging.info(f"✗ Failed: {len(failed_reports)} - {failed_reports[:5]}{'...' if len(failed_reports) > 5 else ''}")
            if timed_out_reports:
                logging.info(f"⏱ Timed out: {len(timed_out_reports)} - {timed_out_reports}")
            logging.info(f"{'='*60}")

        finally:
            # Clean up temp settings file
            import os
            try:
                os.unlink(settings_path)
            except Exception:
                pass

        # Send mails (note: mails are sent by worker processes, not collected here)
        logging.info(f'{datetime.now(tz=pytz.timezone("Europe/Brussels"))}: parallel execution complete')

    @staticmethod
    def _run_report_subprocess(report_name: str, settings_path: str, timeout_seconds: int) -> dict:
        """Run a report in a subprocess with timeout protection.

        Args:
            report_name: Name of report to run (e.g., 'Report0002')
            settings_path: Path to JSON settings file
            timeout_seconds: Maximum execution time in seconds

        Returns:
            Dictionary with keys: 'status' ('success', 'timeout', 'error'), 'error' (if failed)
        """
        import subprocess

        cmd = [
            'python', '-m', 'lib.reports.worker',
            '--report', report_name,
            '--settings', settings_path
        ]

        try:
            result = subprocess.run(
                cmd,
                timeout=timeout_seconds,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {'status': 'success'}
            else:
                return {
                    'status': 'error',
                    'error': result.stderr or 'Non-zero exit code'
                }

        except subprocess.TimeoutExpired:
            return {'status': 'timeout'}

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

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
