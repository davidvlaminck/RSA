import logging
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.mail.MailSender import MailSender
from lib.connectors.Neo4JConnector import SingleNeo4JConnector
from Reports.Report0016 import Report0016
from outputs.sheets_wrapper import SingleSheetsWrapper

if __name__ == '__main__':
    logging.info = print
    logging.basicConfig(filename='logs.txt',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)
    service_cred_path = os.environ.get('RSA_SHEETS_SERVICE_ACCOUNT', '')
    if not service_cred_path:
        raise RuntimeError('Set RSA_SHEETS_SERVICE_ACCOUNT to a Google Sheets service-account JSON path')
    SingleSheetsWrapper.init(service_cred_path=service_cred_path, readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")
    mail_sender = MailSender()
    report_instance = Report0016()
    report_instance.init_report()
    report_instance.run_report(sender=mail_sender)
    mail_sender.send_all_mails()
