from outputs.base import OutputWriteContext
from outputs.excel import ExcelOutput
from outputs.report_routes import report_bucket_name, report_sharepoint_url
from lib.mail.MailSender import MailSender


class DummyQR:
    def __init__(self, rows, keys=None, last_data_update=None):
        self.rows = rows
        self._keys = keys or ['uuid', 'naam']
        self.last_data_update = last_data_update

    @property
    def keys(self):
        return self._keys

    def iter_rows(self):
        yield from self.rows


def test_bucket_name_ranges():
    assert report_bucket_name(0) == '0000-0099'
    assert report_bucket_name(99) == '0000-0099'
    assert report_bucket_name(100) == '0100-0199'
    assert report_bucket_name(201) == '0200-0299'


def test_excel_write_report_uses_bucket_folder(tmp_path):
    out_dir = tmp_path / 'out'
    writer = ExcelOutput(output_dir=str(out_dir))
    qr = DummyQR([['a', '1']])
    ctx = OutputWriteContext(
        spreadsheet_id='x',
        report_title='bucketed report',
        datasource_name='ArangoDB',
        now_utc='now',
        report_name='report0201',
        excel_filename='[RSA] Example report.xlsx',
    )

    meta = writer.write_report(ctx, qr)

    assert meta is not None
    expected = out_dir / '0200-0299' / '[RSA] Example report.xlsx'
    assert expected.exists()
    assert writer._resolve_workbook_path('[RSA] Example report.xlsx') == expected


def test_sharepoint_url_is_bucketed():
    url = report_sharepoint_url(
        excel_filename='[RSA] Example report.xlsx',
        report_name='report0201',
        report_title='Example report',
    )
    assert url is not None
    assert '/0200-0299/' in url
    assert '%5BRSA%5D%20Example%20report.xlsx' in url
    assert url.endswith('?web=1')


def test_mail_sender_uses_sharepoint_link():
    sender = MailSender(mail_settings={'host': 'localhost', 'username': 'u', 'password': 'p'})
    sender.add_mail(
        receiver='david.vlaminck@mow.vlaanderen.be',
        report_name='Example report',
        spreadsheet_id='sheet-id',
        count=5,
        latest_sync='2026-04-01 12:00:00',
        frequency='Dagelijks',
        excel_filename='[RSA] Example report.xlsx',
        report_code='report0201',
    )

    content = sender.mails_to_send[0]
    assert content.hyperlink is not None
    assert '/0200-0299/' in content.hyperlink
    assert content.hyperlink.endswith('?web=1')

