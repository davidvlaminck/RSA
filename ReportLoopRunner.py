import importlib
import importlib.util
# initialize a SheetsWrapper through SingleSheetsWrapper
# same for Neo4JConnector and other connectors
# then run reports that use the Single version of the class to get the initialized version
import logging
import os
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

import pytz

from MailContent import MailContent
from MailSender import MailSender
from Neo4JConnector import SingleNeo4JConnector
from PostGISConnector import SinglePostGISConnector
from SettingsManager import SettingsManager
from SheetsWrapper import SingleSheetsWrapper

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))
BRUSSELS = ZoneInfo("Europe/Brussels")


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
        start_hms = time_cfg.get('start', '03:00:00')
        end_hms = time_cfg.get('end', '23:59:59')
        return self._parse_hms_to_seconds(start_hms), self._parse_hms_to_seconds(end_hms)

    def _is_within_run_window(self, now: datetime) -> bool:
        start_s, end_s = self._get_run_window()
        now_s = now.hour * 3600 + now.minute * 60 + now.second
        if start_s <= end_s:
            return start_s <= now_s <= end_s
        return now_s >= start_s or now_s <= end_s

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
        """Return (start_seconds, end_seconds) from settings. Defaults keep existing behavior."""
        time_cfg = self.settings.get('time', {}) if isinstance(self.settings, dict) else {}

        # Backward-compatible defaults:
        # - old behavior: don't start until 03:00, no explicit end.
        start_hms = time_cfg.get('start', '03:00:00')
        end_hms = time_cfg.get('end', '23:59:59')

        return self._parse_hms_to_seconds(start_hms), self._parse_hms_to_seconds(end_hms)

    def _is_within_run_window(self, now: datetime) -> bool:
        start_s, end_s = self._get_run_window()
        now_s = now.hour * 3600 + now.minute * 60 + now.second

        # Support windows that cross midnight (e.g. 23:00 -> 02:00)
        if start_s <= end_s:
            return start_s <= now_s <= end_s
        return now_s >= start_s or now_s <= end_s

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
        # start running reports now and at midnight
        logging.info(f"{datetime.now(tz=BRUSSELS)}: let's run the reports now")

        # detect reports in Reports directory
        self.reports = []
        for file in os.listdir(self.dir_path):
            if file.endswith('.py'):
                self.reports.append(file[:-3])

        reports_to_do = sorted(self.reports)
        reports_run = 0

        while reports_run < 5 and len(reports_to_do) > 0:
            reports_run += 1
            for report_name in sorted(reports_to_do):
                try:
                    report_instance = self.dynamic_create_instance_from_name(report_name)
                    report_instance.init_report()
                    # set pipeline-wide defaults (reports can override)
                    if hasattr(report_instance, 'report') and report_instance.report is not None:
                        if hasattr(report_instance.report, 'output'):
                            report_instance.report.output = self.output_type
                        if hasattr(report_instance.report, 'output_settings'):
                            report_instance.report.output_settings = self.output_settings
                    report_instance.run_report(sender=self.mail_sender)
                    reports_to_do.remove(report_name)
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
                     f'sent all mails_to_send ({len(self.mail_sender.mails_to_send)})')

    @staticmethod
    def dynamic_create_instance_from_name(report_name):
        try:
            module_spec = importlib.util.find_spec(f'Reports.{report_name}')
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            class_ = getattr(module, report_name)
            return class_()
        except ModuleNotFoundError as exc:
            logging.error(exc.msg)

    @staticmethod
    def adjust_mailed_info_in_sheets(sender: MailSender):
        sent_mails = sender.sent_mails
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
