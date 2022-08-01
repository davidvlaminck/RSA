from dataclasses import dataclass
from datetime import datetime


@dataclass
class MailContent:
    receiver: str = ''
    hyperlink: str = ''
    report_name: str = ''
    count: int = -1
    latest_sync: str = ''
    frequency: str = ''
    spreadsheet_id: str = ''
    mail_sent: datetime = None
