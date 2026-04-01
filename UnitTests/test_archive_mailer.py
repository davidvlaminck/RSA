import sys
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from unittest.mock import patch
import zipfile

# Ensure project root is on sys.path so tests can import local modules like `lib`
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from lib.mail.archive_mailer import create_output_archive, send_archive_email, zip_and_mail_output_dir


def test_create_output_archive_zips_directory_contents():
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / 'RSA_OneDrive'
        source.mkdir()
        (source / 'file1.txt').write_text('alpha', encoding='utf-8')
        nested = source / 'nested'
        nested.mkdir()
        (nested / 'file2.txt').write_text('beta', encoding='utf-8')

        archive_path = create_output_archive(source)
        try:
            assert archive_path.name == 'reports.zip'
            with zipfile.ZipFile(archive_path) as zf:
                assert sorted(zf.namelist()) == ['file1.txt', 'nested/file2.txt']
        finally:
            shutil.rmtree(archive_path.parent, ignore_errors=True)


@patch('lib.mail.archive_mailer.smtplib.SMTP')
def test_send_archive_email_sends_zip_attachment(mock_smtp):
    with TemporaryDirectory() as tmp:
        archive = Path(tmp) / 'test.zip'
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('inside.txt', 'hello')

        send_archive_email(
            mail_settings={'host': 'smtp.example.test', 'username': 'user', 'password': 'secret'},
            recipient='david.vlaminck@mow.vlaanderen.be',
            archive_path=archive,
            subject='Test archive',
        )

        smtp_instance = mock_smtp.return_value.__enter__.return_value
        smtp_instance.login.assert_called_once_with(user='user', password='secret')
        smtp_instance.send_message.assert_called_once()
        message = smtp_instance.send_message.call_args.args[0]
        attachments = list(message.iter_attachments())
        assert len(attachments) == 1
        assert attachments[0].get_filename() == 'test.zip'
        assert message['To'] == 'david.vlaminck@mow.vlaanderen.be'


@patch('lib.mail.archive_mailer.smtplib.SMTP')
def test_zip_and_mail_output_dir_removes_temp_archive_by_default(mock_smtp):
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / 'RSA_OneDrive'
        source.mkdir()
        (source / 'report.xlsx').write_text('dummy', encoding='utf-8')

        result = zip_and_mail_output_dir(
            output_dir=source,
            mail_settings={'host': 'smtp.example.test', 'username': 'user', 'password': 'secret'},
            recipient='david.vlaminck@mow.vlaanderen.be',
        )

        assert result is None
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()
        smtp_message = mock_smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        attachment = list(smtp_message.iter_attachments())[0]
        assert attachment.get_filename() == 'reports.zip'


