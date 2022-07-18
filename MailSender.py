import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import socks


@dataclass
class MailContent:
    receiver: str = ''
    hyperlink: str = ''
    report_name: str = ''
    count: int = -1
    latest_sync: str = ''


class MailSender:
    def __init__(self):
        socks.setdefaultproxy(socks.SOCKS5, 'proxy.vlaanderen.be', 8080)
        socks.wrapmodule(smtplib)
        self.mails: [MailContent] = []

    def add_mail(self, receiver: str, report_name: str, spreadsheet_id: str, count: int, latest_sync: str):
        content = MailContent(receiver=receiver, count=count, latest_sync=latest_sync, report_name=report_name)
        content.hyperlink = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
        self.mails.append(content)

    def send_all_mails(self):
        sorted_mail_content = {}
        server = smtplib.SMTP('smtp.vlaanderen.be')
        # server.set_debuglevel(1)

        for mailcontent in self.mails:
            sorted_mail_content.setdefault(mailcontent.receiver, []).append(mailcontent)

        for receiver, mails in sorted_mail_content.items():
            # combine content
            sender = 'david.vlaminck@mow.vlaanderen.be'

            html = '<html><head><style>' \
                   'table, th, td { border: 1px solid black; border-collapse: collapse; text-align: left }' \
                   'th, td { padding: 5px; }' \
                   '</style></head><body>' \
                   '<p>U ontvangt hierbij een samenvatting van de rapporten die door Rapporteringsservice Assets werd uitgevoerd.<p>' \
                   '<table><tr><th>Rapport Link</th><th>Aantal</th><th>Data van</th></tr>'

            for mail_content in mails:
                html += f'<tr><td><a href="{mail_content.hyperlink}">{mail_content.report_name}</a></td>' \
                        f'<td>{str(mail_content.count)}</td><td>{mail_content.latest_sync}</td>'

            html += '</table></body></html>'
            email_message = MIMEMultipart()
            email_message['From'] = f'Rapporteringsservice Assets <{sender}>'
            email_message['To'] = receiver
            email_message['Subject'] = f'Rapporteringsservice Assets overzicht'

            email_message.attach(MIMEText(html, "html"))
            msg = email_message.as_string()

            server.sendmail(sender, receiver, msg)

        server.quit()

