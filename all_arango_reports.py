import importlib
import importlib.util
import logging
import os
import traceback
from datetime import datetime, UTC
from lib.mail.MailSender import MailSender
from SettingsManager import SettingsManager
from outputs.sheets_wrapper import SingleSheetsWrapper
from Neo4JConnector import SingleNeo4JConnector
from PostGISConnector import SinglePostGISConnector

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))

# List of Arango reports to run, based on tasks.md (Has AQL Query = Yes, Refactored = Yes)
ARANGO_REPORTS = [
    'Report0002', 'Report0003', 'Report0004', 'Report0005', 'Report0006', 'Report0007',
    'Report0009', 'Report0010', 'Report0012', 'Report0013', 'Report0014', 'Report0015',
    'Report0016', 'Report0017', 'Report0018', 'Report0019', 'Report0020', 'Report0023',
    'Report0024', 'Report0025', 'Report0026', 'Report0032', 'Report0033', 'Report0034',
    'Report0037', 'Report0038', 'Report0040', 'Report0041', 'Report0042', 'Report0045',
    'Report0046'
]

class AllArangoReportsRunner:
    def __init__(self, settings_path):
        settings_manager = SettingsManager(settings_path=settings_path)
        self.settings = settings_manager.settings

        logging.info = print
        logging.basicConfig(filename='logs.txt',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
        try:
            SingleSheetsWrapper.init(service_cred_path=self.settings['google_api']['credentials_path'],
                                     readonly_scope=False)
        except Exception as e:
            logging.error(f"Failed to initialize SingleSheetsWrapper: {e}")
            traceback.print_exc()

        try:
            neo4j_settings = self.settings['databases']['Neo4j']
            SingleNeo4JConnector.init(uri=neo4j_settings['uri'], user=neo4j_settings['user'],
                                      password=neo4j_settings['password'], database=neo4j_settings['database'])
        except Exception as e:
            logging.error(f"Failed to initialize SingleNeo4JConnector: {e}")
            traceback.print_exc()

        try:
            postgis_settings = self.settings['databases']['PostGIS']
            SinglePostGISConnector.init(host=postgis_settings['host'], port=postgis_settings['port'],
                                        user=postgis_settings['user'], password=postgis_settings['password'],
                                        database=postgis_settings['database'])
        except Exception as e:
            logging.error(f"Failed to initialize SinglePostGISConnector: {e}")
            traceback.print_exc()

        try:
            arango_settings = self.settings['databases']['ArangoDB']
            from datasources.arango import SingleArangoConnector
            SingleArangoConnector.init(
                host=arango_settings['host'],
                port=arango_settings['port'],
                user=arango_settings['user'],
                password=arango_settings['password'],
                database=arango_settings['database']
            )
        except Exception as e:
            logging.error(f"Failed to initialize SingleArangoConnector: {e}")
            traceback.print_exc()

        self.dir_path = os.path.abspath(os.path.join(os.sep, ROOT_DIR, 'Reports'))
        self.mail_sender = MailSender(mail_settings=self.settings['smtp_options'])

    def run(self):
        started_running_date = None
        now_utc = datetime.now(UTC)
        started_running_date = now_utc.date()
        logging.info(f'{now_utc}: running all Arango reports')
        reports_to_do = list(ARANGO_REPORTS)
        for report_name in sorted(reports_to_do):
            try:
                report_instance = self.dynamic_create_instance_from_name(report_name)
                report_instance.init_report()
                report_instance.run_report(sender=self.mail_sender)
                logging.info(f"Completed report: {report_name}")
            except Exception as ex:
                logging.info(f"Exception in report {report_name}: {ex}")
                logging.exception(ex)
                traceback.print_exc()
                logging.error(f'Failed completing report {report_name}')
        logging.info(f'{datetime.now(UTC)}: done running all Arango reports')
        try:
            self.mail_sender.send_all_mails()
            self.adjust_mailed_info_in_sheets(sender=self.mail_sender)
            logging.info(f'{datetime.now(UTC)}: sent all mails_to_send ({len(self.mail_sender.mails_to_send)})')
        except Exception as ex:
            logging.info(f"Mail sending failed: {ex}")
            logging.exception(ex)

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
        for mailcontent in sent_mails:
            if not hasattr(mailcontent, 'spreadsheet_id'):
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
    runner = AllArangoReportsRunner(
        settings_path=r'/home/david/Documents/AWV/resources/settings_RSA.json')
    runner.run()
