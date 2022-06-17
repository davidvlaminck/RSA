import importlib
import importlib.util
import os

# initialize a SheetsWrapper through SingleSheetsWrapper
# same for Neo4JConnector and other connectors
# then run reports that use the Single.. version of the class to get the initialized version
import logging
import time
from datetime import datetime
from os.path import exists

from MailSender import MailSender
from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

ROOT_DIR = (os.path.dirname(os.path.abspath(__file__)))


class ReportLoopRunner:
    def __init__(self):
        logging.info = print
        logging.basicConfig(filename='logs.txt',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)
        SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                                 readonly_scope=False)
        SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

        self.reports = None
        self.dir_path = os.path.abspath(os.path.join(os.sep, ROOT_DIR, 'Reports'))
        self.mail_sender = MailSender()

    def run(self):
        started_running_date = None

        while True:
            if started_running_date is None or started_running_date != (datetime.utcnow()).date():
                # start running reports at midnight
                logging.info(f'{datetime.now()}: let\'s run the reports now')
                started_running_date = (datetime.utcnow()).date()

                # detect reports in Reports directory
                self.reports = []
                for file in os.listdir(self.dir_path):
                    if file.endswith('0016.py'):
                        self.reports.append(file.replace('.py', ''))

                for report_name in self.reports:
                    try:
                        report_instance = self.dynamic_create_instance_from_name(report_name)
                        report_instance.init_report()
                        report_instance.run_report(sender=self.mail_sender)
                    except Exception as ex:
                        logging.exception(ex)
                logging.info(f'{datetime.now()}: done running the reports')

                self.mail_sender.send_all_mails()
            else:
                logging.info(f'{datetime.now()}: not yet the right time to run reports.')
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
            print(exc.msg)
            pass




