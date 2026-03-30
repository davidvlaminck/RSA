import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.reports.DQReport import DQReport
from lib.mail.MailSender import MailSender

if __name__ == '__main__':
    mailer = MailSender()
    receivers = ['davidvlaminck85@gmail.com', 'david.vlaminck@mow.vlaanderen.be']
    sender = 'david.vlaminck@belfla.be'
    msg = "From: Rapporteringsservice <david.vlaminck@belfla.be>\r\nTo: davidvlaminck85@gmail.com, david.vlaminck@mow.vlaanderen.be\r\nSubject: Testmail\r\ntest message\r\nline2"
    mail_hostname = 'mail.belfla.be'
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=mailer, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                      previous_result=0, result=1)
    mailer.send_all_mails()

    pass
