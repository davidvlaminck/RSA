import smtplib
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class MailContent:
    receiver: str = ''
    hyperlink: str = ''
    report_name: str = ''
    count: int = -1
    latest_sync: str = ''


class MailSender:
    def __init__(self):
        self.mails: [MailContent] = []

    def add_mail(self, receiver: str, report_name: str, spreadsheet_id: str, count: int, latest_sync: str):
        content = MailContent(receiver=receiver, count=count, latest_sync=latest_sync, report_name=report_name)
        content.hyperlink = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
        self.mails.append(content)

    def send_all_mails(self):
        sorted_mail_content = {}
        server = smtplib.SMTP('smtp.vlaanderen.be')
        server.set_debuglevel(1)

        for mailcontent in self.mails:
            sorted_mail_content.setdefault(mailcontent.receiver, []).append(mailcontent)

        for receiver, mails in sorted_mail_content.items():
            # combine content
            receivers = [receiver]
            sender = 'david.vlaminck@mow.vlaanderen.be'
            msglines = ['From: Rapporteringsservice Assets <david.vlaminck@mow.vlaanderen.be>', f'To: {receiver}',
                        'Subject: Rapporteringsservice Assets overzicht',
                        'U ontvangt hierbij een samenvatting van de rapporten die door Rapporteringsservice Assets werd uitgevoerd.',
                        '']
            for mail_content in mails:
                msglines.append(f'<a href="{mail_content.hyperlink}">{mail_content.report_name}</a> heeft '
                                f'{str(mail_content.count)} records op basis van de data van {mail_content.latest_sync}')

            msg = '\r\n'.join(msglines)

            server.sendmail(sender, receivers, msg)

        server.quit()

