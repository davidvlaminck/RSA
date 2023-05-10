import importlib
import importlib.util
# initialize a SheetsWrapper through SingleSheetsWrapper
# same for Neo4JConnector and other connectors
# then run reports that use the Single version of the class to get the initialized version
import logging
import os
import time
from datetime import datetime

from MailContent import MailContent
from MailSender import MailSender
from Neo4JConnector import SingleNeo4JConnector
from PostGISConnector import SinglePostGISConnector
from SettingsManager import SettingsManager
from SheetsWrapper import SingleSheetsWrapper

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))


class SingleReportLoopRunner:
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

    def run(self, report: str):
        started_running_date = None

        while True:
            if started_running_date is None or started_running_date != (datetime.utcnow()).date():
                # start running reports at midnight
                logging.info(f'{datetime.utcnow()}: let\'s run the reports now')
                started_running_date = (datetime.utcnow()).date()

                # detect reports in Reports directory
                self.reports = [report]

                reports_to_do = sorted(self.reports)
                reports_run = 0

                while reports_run < 5 and len(reports_to_do) > 0:
                    reports_run += 1
                    for report_name in sorted(reports_to_do):
                        try:
                            report_instance = self.dynamic_create_instance_from_name(report_name)
                            report_instance.init_report()
                            report_instance.run_report(sender=self.mail_sender)
                            reports_to_do.remove(report_name)
                        except Exception as ex:
                            logging.info(f"exception happened in report {report_name}: {ex}")
                            logging.exception(ex)
                            logging.error(f'failed completing report {report_name}')
                    logging.info(
                        f'{datetime.utcnow()}: done running report loop {reports_run}. Reports left to do: {len(reports_to_do)}')

                logging.info(f'{datetime.utcnow()}: done running the reports')

                self.mail_sender.send_all_mails()
                self.adjust_mailed_info_in_sheets(sender=self.mail_sender)

                logging.info(f'{datetime.utcnow()}: sent all mails_to_send ({len(self.mail_sender.mails_to_send)})')
            else:
                logging.info(f'{datetime.utcnow()}: not yet the right time to run reports.')
                time.sleep(60)

    @staticmethod
    def dynamic_create_instance_from_name(report_name):
        try:
            module_spec = importlib.util.find_spec(f'Reports.{report_name}')
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            class_ = getattr(module, report_name)
            instance = class_()
            return instance
        except ModuleNotFoundError as exc:
            logging.error(exc.msg)
            pass

    @staticmethod
    def adjust_mailed_info_in_sheets(sender: MailSender):
        sent_mails = sender.sent_mails
        sheet_info = sender.sheet_info
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        # loop through sent_mails
        # if item is in sheet_info, adjust cell

        for mailcontent in sent_mails:
            if not isinstance(mailcontent, MailContent):
                continue
            sheet_id = mailcontent.spreadsheet_id
            if sheet_id not in sheet_info:
                continue
            found_infos = list(filter(lambda info: info['mail'] == mailcontent.receiver and
                                                   info['frequency'] == mailcontent.frequency, sheet_info[sheet_id]))
            for found_info in found_infos:
                sheets_wrapper.write_data_to_sheet(spreadsheet_id=sheet_id, start_cell=found_info['cell'],
                                                   sheet_name='Overzicht',
                                                   data=[[mailcontent.mail_sent.strftime("%Y-%m-%d %H:%M:%S")]])


if __name__ == '__main__':
    reportlooprunner = SingleReportLoopRunner(
        settings_path=r'/home/davidlinux/Documents/AWV/resources/settings_RSA.json')
    # reportlooprunner = SingleReportLoopRunner(settings_path=r'C:\resources\settings_RSA.json')
    reportlooprunner.run(report='Report0064')
