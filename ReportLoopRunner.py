import os

# initialize a SheetsWrapper through SingleSheetsWrapper
# same for Neo4JConnector and other connectors
# then run reports that use the Single.. version of the class to get the initialized version
import logging
import time
from datetime import datetime
from os.path import exists

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
                    if file.endswith('.py'):
                        self.reports.append(os.path.join(self.dir_path, file))

                for report_location in self.reports:
                    try:
                        o = open(report_location)
                        r = o.read()
                        exec(r)
                    except Exception as ex:
                        logging.exception(ex)
                logging.info(f'{datetime.now()}: done running the reports')
            else:
                logging.info(f'{datetime.now()}: not yet the right time to run reports.')
                time.sleep(60)




