import logging
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from MailContent import MailContent


class MailSender:
    def __init__(self, mail_settings: dict):
        self.mails_to_send: [MailContent] = []
        self.host = mail_settings['host']
        self.username = mail_settings['username']
        self.password = mail_settings['password']
        self.sent_mails: [MailContent] = []
        self.sheet_info = {}

    def add_mail(self, receiver: str, report_name: str, spreadsheet_id: str, count: int, latest_sync: str,
                 frequency: str, previous: int = -1):
        content = MailContent(receiver=receiver, count=count, latest_sync=latest_sync, report_name=report_name,
                              frequency=frequency, spreadsheet_id=spreadsheet_id, previous=previous)
        content.hyperlink = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
        self.mails_to_send.append(content)

    def send_all_mails(self):
        self.sent_mails = []
        sorted_mail_content = {}
        server = smtplib.SMTP(host=self.host)

        server.login(user=self.username, password=self.password)

        for mailcontent in self.mails_to_send:
            sorted_mail_content.setdefault(mailcontent.receiver, []).append(mailcontent)

        mail_counter = 0
        for receiver, mails in sorted_mail_content.items():
            # combine content
            sender = self.username

            html = '<html><head><style>' \
                   'table, th, td { border: 1px solid black; border-collapse: collapse; text-align: left }' \
                   'th, td { padding: 5px; }' \
                   '</style></head><body>' \
                   '<p>U ontvangt hierbij een samenvatting van de rapporten die door Rapporteringsservice Assets werd uitgevoerd.<p>' \
                   '<table><tr><th>Rapport Link</th><th>Vorig aantal</th><th>Aantal</th><th>Data van</th></tr>'

            for mail_content in self.remove_duplicate_mail_content(mails):
                html += f'<tr><td><a href="{mail_content.hyperlink}">{mail_content.report_name}</a></td>'
                if mail_content.previous == -1:
                    html += '<td></td>'
                else:
                    html += f'<td>{str(mail_content.previous)}</td>'
                html += f'<td>{str(mail_content.count)}</td><td>{mail_content.latest_sync}</td>'

            html += '</table></body></html>'
            email_message = MIMEMultipart()
            email_message['From'] = f'Rapporteringsservice Assets <{sender}>'
            email_message['To'] = receiver
            email_message['Subject'] = f'Rapporteringsservice Assets overzicht'

            email_message.attach(MIMEText(html, "html"))
            msg = email_message.as_string()

            try:
                server.sendmail(sender, receiver, msg)
                mail_counter += 1
                if mail_counter > 90:
                    mail_counter = 0
                    time.sleep(300) # avoid spam limit
                for mail_content in mails:
                    mail_content.mail_sent = datetime.utcnow()
                self.sent_mails.extend(mails)
            except:
                logging.error(f'Could not send an email to {receiver}')

        server.quit()
        self.mails_to_send = []

    def add_sheet_info(self, spreadsheet_id: str, mail_receivers_dict: [dict]):
        self.sheet_info[spreadsheet_id] = mail_receivers_dict
        # store all the sheet info

    @staticmethod
    def remove_duplicate_mail_content(mails):
        no_duplicate_content = []
        for mail in mails:
            mail_found = list(filter(lambda c: c.report_name == mail.report_name and c.latest_sync == mail.latest_sync,
                                     no_duplicate_content))
            if len(mail_found) > 0:
                continue
            no_duplicate_content.append(mail)
        return no_duplicate_content
