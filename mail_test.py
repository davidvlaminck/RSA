from DQReport import DQReport
from MailSender import MailSender

if __name__ == '__main__':
    mailer = MailSender()
    receivers = ['davidvlaminck85@gmail.com', 'david.vlaminck@mow.vlaanderen.be']
    sender = 'david.vlaminck@belfla.be'
    msg = "From: Rapporteringsservice <david.vlaminck@belfla.be>\r\nTo: davidvlaminck85@gmail.com, david.vlaminck@mow.vlaanderen.be\r\nSubject: Testmail\r\ntest message\r\nline2"
    report = DQReport(name='test report', title='test report title', spreadsheet_id='testsheetId')
    report.send_mails(sender=mailer, named_range=[['david.vlaminck@mow.vlaanderen.be', 'Dagelijks', '2022-01-01 01:00:00']],
                      previous_result=0, result=1)
    mailer.send_all_mails()

    pass