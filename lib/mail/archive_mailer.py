from __future__ import annotations

import logging
import smtplib
import shutil
import tempfile
import zipfile
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Union


FIXED_SUBJECT = 'RSA'
DEFAULT_BODY = (
    'In bijlage vindt u het zip-archief van de inhoud van RSA_OneDrive, '
    'gegenereerd na het afronden van de rapporten.'
)


def create_output_archive(source_dir: Union[str, Path]) -> Path:
    """Zip the contents of source_dir into a temporary archive named reports.zip and return its path."""
    source_path = Path(source_dir).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f'Output directory does not exist: {source_path}')
    if not source_path.is_dir():
        raise NotADirectoryError(f'Output path is not a directory: {source_path}')

    temp_dir = Path(tempfile.mkdtemp(prefix='rsa_reports_'))
    archive_path = temp_dir / 'reports.zip'

    with zipfile.ZipFile(archive_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(source_path.rglob('*')):
            if not file_path.is_file():
                continue
            zf.write(file_path, arcname=file_path.relative_to(source_path))

    return archive_path


def send_archive_email(
    *,
    mail_settings: dict,
    recipient: str,
    archive_path: Union[str, Path],
    subject: Optional[str] = None,
    body: str = DEFAULT_BODY,
) -> None:
    """Send a zip archive as attachment using the project's SMTP settings."""
    archive = Path(archive_path).expanduser().resolve()
    if not archive.exists():
        raise FileNotFoundError(f'Archive not found: {archive}')

    host = mail_settings['host']
    username = mail_settings['username']
    password = mail_settings['password']
    port = int(mail_settings.get('port', 25))
    use_starttls = bool(mail_settings.get('starttls', False))
    from_address = mail_settings.get('from_address', username)
    from_name = mail_settings.get('from_name', 'Rapporteringsservice Assets')

    message = EmailMessage()
    message['From'] = f'{from_name} <{from_address}>'
    message['To'] = recipient
    # Subject is fixed by requirement, regardless of caller input.
    message['Subject'] = FIXED_SUBJECT
    message.set_content(body)
    message.add_attachment(
        archive.read_bytes(),
        maintype='application',
        subtype='zip',
        filename=archive.name,
    )

    with smtplib.SMTP(host=host, port=port, timeout=60) as server:
        if use_starttls:
            server.starttls()
        if username and password:
            server.login(user=username, password=password)
        server.send_message(message)

    logging.info('Archive email sent to %s with attachment %s', recipient, archive)


def zip_and_mail_output_dir(
    *,
    output_dir: Union[str, Path],
    mail_settings: dict,
    recipient: str,
    subject: Optional[str] = None,
    body: str = DEFAULT_BODY,
    keep_archive: bool = False,
) -> Optional[Path]:
    """Create a temporary zip of output_dir and email it to recipient.

    Returns the archive path if keep_archive=True, otherwise removes it and returns None.
    """
    archive_path = create_output_archive(output_dir)
    try:
        size_mb = archive_path.stat().st_size / (1024 * 1024)
        if size_mb > 20:
            logging.warning('Archive is %.1f MB; some SMTP servers may reject large attachments.', size_mb)
        send_archive_email(
            mail_settings=mail_settings,
            recipient=recipient,
            archive_path=archive_path,
            subject=subject,
            body=body,
        )
        if keep_archive:
            return archive_path
        return None
    finally:
        if not keep_archive:
            try:
                shutil.rmtree(archive_path.parent, ignore_errors=True)
            except Exception as ex:
                logging.warning('Could not remove temporary archive %s: %s', archive_path, ex)






