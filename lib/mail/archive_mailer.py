from __future__ import annotations

import logging
import smtplib
import shutil
import tempfile
import time
import zipfile
from email.message import EmailMessage
from pathlib import Path
from typing import Optional, Union


FIXED_SUBJECT = 'RSA'
DEFAULT_BODY = (
    'In bijlage vindt u het zip-archief van de inhoud van RSA_OneDrive, '
    'gegenereerd na het afronden van de rapporten.'
)
MAX_ATTACHMENT_MB = 25
MAIL_DELAY_SECONDS = 60


def _gather_files(source_dir: Union[str, Path]) -> tuple[Path, list[Path]]:
    source_path = Path(source_dir).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f'Output directory does not exist: {source_path}')
    if not source_path.is_dir():
        raise NotADirectoryError(f'Output path is not a directory: {source_path}')

    files = [p for p in sorted(source_path.rglob('*')) if p.is_file()]
    return source_path, files


def _write_archive(source_path: Path, files: list[Path], destination: Path) -> None:
    with zipfile.ZipFile(destination, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, arcname=file_path.relative_to(source_path))


def _split_files_by_size(files: list[Path], max_bytes: int) -> list[list[Path]]:
    batches: list[list[Path]] = []
    current: list[Path] = []
    current_size = 0

    for file_path in files:
        file_size = file_path.stat().st_size
        # keep margin for zip headers and metadata
        predicted = file_size + 1024
        if current and current_size + predicted > max_bytes:
            batches.append(current)
            current = []
            current_size = 0
        current.append(file_path)
        current_size += predicted

    if current:
        batches.append(current)

    if not batches:
        batches = [[]]

    return batches


def create_output_archives(source_dir: Union[str, Path], *, max_attachment_mb: int = MAX_ATTACHMENT_MB) -> list[Path]:
    """Create one or more zip archives named reports.zip (one per part folder)."""
    max_bytes = max_attachment_mb * 1024 * 1024
    source_path, files = _gather_files(source_dir)

    temp_dir = Path(tempfile.mkdtemp(prefix='rsa_reports_'))
    batches = _split_files_by_size(files, max_bytes=max_bytes)
    archives: list[Path] = []

    for idx, batch in enumerate(batches, start=1):
        part_dir = temp_dir / f'part_{idx:03d}'
        part_dir.mkdir(parents=True, exist_ok=True)
        archive_path = part_dir / 'reports.zip'
        _write_archive(source_path, batch, archive_path)
        archive_size = archive_path.stat().st_size
        if archive_size > max_bytes:
            raise ValueError(
                f'Archive part {idx} is {archive_size} bytes and exceeds max {max_bytes} bytes. '
                'Consider increasing max_attachment_mb or reducing source file sizes.'
            )
        archives.append(archive_path)

    return archives


def create_output_archive(source_dir: Union[str, Path]) -> Path:
    """Backward-compatible helper returning the first generated archive."""
    return create_output_archives(source_dir, max_attachment_mb=MAX_ATTACHMENT_MB)[0]


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

    max_attachment_mb: int = MAX_ATTACHMENT_MB,
    delay_between_emails_seconds: int = MAIL_DELAY_SECONDS,
) -> Optional[list[Path]]:
    """Create one or more zips of output_dir and email them sequentially.

    Each sent zip is independently extractable.
    Returns archive paths if keep_archive=True, otherwise removes temp data and returns None.
    """
    archive_paths = create_output_archives(output_dir, max_attachment_mb=max_attachment_mb)
    total_parts = len(archive_paths)
    root_temp_dir = archive_paths[0].parents[1]

    try:
        for idx, archive_path in enumerate(archive_paths, start=1):
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            logging.info('Preparing archive part %s/%s (%.1f MB): %s', idx, total_parts, size_mb, archive_path)
            part_body = f'{body}\n\nDeel {idx} van {total_parts}. Elk deel is afzonderlijk uitpakbaar.'
            send_archive_email(
                mail_settings=mail_settings,
                recipient=recipient,
                archive_path=archive_path,
                subject=subject,
                body=part_body,
            )
            if idx < total_parts and delay_between_emails_seconds > 0:
                logging.info('Waiting %s seconds before sending next archive mail', delay_between_emails_seconds)
                time.sleep(delay_between_emails_seconds)

        if keep_archive:
            return archive_paths
        return None
    finally:
        if not keep_archive:
            try:
                shutil.rmtree(root_temp_dir, ignore_errors=True)
            except Exception as ex:
                logging.warning('Could not remove temporary archive directory %s: %s', root_temp_dir, ex)






