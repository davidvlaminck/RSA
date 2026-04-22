"""Google Drive sync helper.

Gebruik:
    1. Eenmalig inloggen via browser:
       python -m scripts.ops.gdrive_upload login \
            --credentials /path/to/external/resources/gdrive_oauth_credentials.json \
            --token      /path/to/external/resources/gdrive_token.pkl

    2. Download mirror (Drive -> local):
       python -m scripts.ops.gdrive_upload sync-down \
           --folder /path/to/RSA_OneDrive \
           --drive-folder RSA_Reports \
            --token /path/to/external/resources/gdrive_token.pkl

    3. Upload mirror (local -> Drive):
       python -m scripts.ops.gdrive_upload sync-up \
           --folder /path/to/RSA_OneDrive \
           --drive-folder RSA_Reports \
            --token /path/to/external/resources/gdrive_token.pkl

Token-levensduur:
    De access token vervalt na 1 uur maar wordt automatisch ververst door de library.
    De refresh token blijft geldig zolang de Google OAuth consent/config actief blijft.
"""
from __future__ import annotations

import argparse
import logging
import pickle
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Full folder mirroring needs broader scope than drive.file.
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_MIME = 'application/vnd.google-apps.folder'
BRUSSELS = ZoneInfo('Europe/Brussels')
SKIP_NAMES = {'archief', 'archivedreports'}


def _should_skip(name: str) -> bool:
    return name.strip().lower() in SKIP_NAMES


def first_login(credentials_json_path: str, token_path: str) -> None:
    """Eenmalige browser-login. Slaat token op voor toekomstig gebruik."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(credentials_json_path, SCOPES)
    creds = flow.run_local_server(port=0)

    token_file = Path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'wb') as fh:
        pickle.dump(creds, fh)

    logging.info('Token opgeslagen: %s', token_path)
    print(f"Ingelogd. Token opgeslagen op: {token_path}")


def _load_credentials(token_path: str) -> Credentials:
    with open(token_path, 'rb') as fh:
        creds: Credentials = pickle.load(fh)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'wb') as fh:
            pickle.dump(creds, fh)

    return creds


def _build_service(token_path: str):
    creds = _load_credentials(token_path)
    return build('drive', 'v3', credentials=creds)


def _safe_name(name: str) -> str:
    return name.replace("'", "\\'")


def _list_children(service, folder_id: str) -> list[dict]:
    rows: list[dict] = []
    page_token = None
    while True:
        result = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token,
            pageSize=1000,
        ).execute()
        rows.extend(result.get('files', []))
        page_token = result.get('nextPageToken')
        if not page_token:
            break
    return rows


def _find_child_by_name(service, parent_id: str, name: str) -> dict | None:
    query = (
        f"name='{_safe_name(name)}' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    result = service.files().list(
        q=query,
        fields='files(id, name, mimeType)',
        pageSize=1,
    ).execute()
    rows = result.get('files', [])
    return rows[0] if rows else None


def _get_or_create_folder(service, folder_name: str, parent_id: str | None = None) -> str:
    query_parts = [
        f"name='{_safe_name(folder_name)}'",
        f"mimeType='{FOLDER_MIME}'",
        'trashed=false',
    ]
    if parent_id:
        query_parts.append(f"'{parent_id}' in parents")

    result = service.files().list(
        q=' and '.join(query_parts),
        fields='files(id, name)',
        pageSize=1,
    ).execute()
    folders = result.get('files', [])
    if folders:
        return folders[0]['id']

    body = {'name': folder_name, 'mimeType': FOLDER_MIME}
    if parent_id:
        body['parents'] = [parent_id]

    folder = service.files().create(body=body, fields='id').execute()
    return folder['id']


def _download_file(service, file_id: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with open(target_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def _download_tree(service, folder_id: str, local_path: Path) -> None:
    local_path.mkdir(parents=True, exist_ok=True)
    for child in _list_children(service, folder_id):
        if _should_skip(child['name']):
            logging.info('Skipping Drive item during download mirror: %s', child['name'])
            continue
        child_path = local_path / child['name']
        if child['mimeType'] == FOLDER_MIME:
            _download_tree(service, child['id'], child_path)
        else:
            _download_file(service, child['id'], child_path)


def _delete_drive_item_recursive(service, item_id: str, mime_type: str) -> None:
    if mime_type == FOLDER_MIME:
        for child in _list_children(service, item_id):
            _delete_drive_item_recursive(service, child['id'], child['mimeType'])
    service.files().delete(fileId=item_id).execute()


def _upload_or_update_file(service, parent_id: str, local_file: Path, existing: dict | None) -> None:
    media = MediaFileUpload(str(local_file), resumable=True)
    if existing and existing.get('mimeType') != FOLDER_MIME:
        service.files().update(fileId=existing['id'], media_body=media).execute()
        logging.info('Drive updated: %s', local_file)
        return

    if existing and existing.get('mimeType') == FOLDER_MIME:
        _delete_drive_item_recursive(service, existing['id'], existing['mimeType'])

    service.files().create(
        body={'name': local_file.name, 'parents': [parent_id]},
        media_body=media,
    ).execute()
    logging.info('Drive uploaded: %s', local_file)


def _sync_local_dir_to_drive(service, local_dir: Path, remote_folder_id: str) -> None:
    remote_children = {child['name']: child for child in _list_children(service, remote_folder_id)}
    local_entries = sorted(local_dir.iterdir(), key=lambda p: p.name)

    for entry in local_entries:
        if _should_skip(entry.name):
            logging.info('Skipping local item during upload mirror: %s', entry)
            continue
        remote = remote_children.pop(entry.name, None)

        if entry.is_dir():
            if remote and remote['mimeType'] != FOLDER_MIME:
                _delete_drive_item_recursive(service, remote['id'], remote['mimeType'])
                remote = None
            if not remote:
                created = service.files().create(
                    body={'name': entry.name, 'mimeType': FOLDER_MIME, 'parents': [remote_folder_id]},
                    fields='id, mimeType',
                ).execute()
                remote = {'id': created['id'], 'mimeType': FOLDER_MIME}
                logging.info('Drive created folder: %s', entry)
            _sync_local_dir_to_drive(service, entry, remote['id'])
            continue

        if entry.is_file():
            _upload_or_update_file(service, remote_folder_id, entry, remote)

    # Delete remote leftovers that do not exist locally anymore.
    for remote_name, remote in remote_children.items():
        _delete_drive_item_recursive(service, remote['id'], remote['mimeType'])
        logging.info('Drive deleted: %s', remote_name)


def sync_drive_to_local(local_folder: str, drive_folder_name: str, token_path: str) -> bool:
    """Mirror Drive folder into local folder (local is replaced)."""
    token_file = Path(token_path)
    if not token_file.exists():
        logging.warning('Drive token niet gevonden: %s', token_path)
        return False

    try:
        service = _build_service(token_path)
        folder_id = _get_or_create_folder(service, drive_folder_name)
    except Exception as exc:
        logging.error('Kon geen verbinding maken met Google Drive: %s', exc)
        return False

    local_path = Path(local_folder)
    if local_path.exists():
        for child in local_path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    local_path.mkdir(parents=True, exist_ok=True)

    try:
        _download_tree(service, folder_id, local_path)
        logging.info("Drive download mirror klaar -> '%s'", drive_folder_name)
        return True
    except Exception as exc:
        logging.error('Drive download mirror mislukt: %s', exc)
        return False


def sync_local_to_drive(local_folder: str, drive_folder_name: str, token_path: str) -> bool:
    """Mirror local folder into Drive folder (Drive is updated/deleted to match local)."""
    token_file = Path(token_path)
    if not token_file.exists():
        logging.warning('Drive token niet gevonden: %s', token_path)
        return False

    local_path = Path(local_folder)
    if not local_path.exists():
        logging.warning('Lokale map niet gevonden: %s', local_folder)
        return False

    try:
        service = _build_service(token_path)
        folder_id = _get_or_create_folder(service, drive_folder_name)
        _sync_local_dir_to_drive(service, local_path, folder_id)
        logging.info("Drive upload mirror klaar -> '%s'", drive_folder_name)
        return True
    except Exception as exc:
        logging.error('Drive upload mirror mislukt: %s', exc)
        return False


def upload_folder_to_drive(
    local_folder: str,
    drive_folder_name: str,
    token_path: str,
    file_extensions: tuple[str, ...] = ('.xlsx',),
) -> None:
    """Legacy helper: upload only top-level files matching file_extensions."""
    token_file = Path(token_path)
    if not token_file.exists():
        logging.warning('Drive token niet gevonden: %s', token_path)
        return

    try:
        service = _build_service(token_path)
        folder_id = _get_or_create_folder(service, drive_folder_name)
    except Exception as exc:
        logging.error('Kon geen verbinding maken met Google Drive: %s', exc)
        return

    local_path = Path(local_folder)
    uploaded = updated = errors = 0

    for filepath in sorted(local_path.iterdir()):
        if not filepath.is_file():
            continue
        if file_extensions and filepath.suffix.lower() not in file_extensions:
            continue

        try:
            existing = _find_child_by_name(service, folder_id, filepath.name)
            if existing and existing.get('mimeType') == FOLDER_MIME:
                _delete_drive_item_recursive(service, existing['id'], existing['mimeType'])
                existing = None

            media = MediaFileUpload(str(filepath), resumable=True)
            if existing:
                service.files().update(fileId=existing['id'], media_body=media).execute()
                updated += 1
            else:
                service.files().create(
                    body={'name': filepath.name, 'parents': [folder_id]},
                    media_body=media,
                ).execute()
                uploaded += 1
        except Exception as exc:
            logging.error('Drive upload mislukt voor %s: %s', filepath.name, exc)
            errors += 1

    logging.info(
        "Drive upload klaar -> '%s': %s nieuw, %s bijgewerkt, %s fouten",
        drive_folder_name,
        uploaded,
        updated,
        errors,
    )


def write_daily_run_log(local_folder: str, status: str, details: str = '') -> Path:
    """Write a dated run log file inside local_folder/logs and return its path."""
    now = datetime.now(BRUSSELS)
    logs_dir = Path(local_folder) / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / f'run_{now:%Y%m%d}.log'
    line = f"{now:%Y-%m-%d %H:%M:%S} | {status}"
    if details:
        line = f"{line} | {details}"
    with open(path, 'a', encoding='utf-8') as fh:
        fh.write(line + '\n')
    return path


def _main() -> None:
    parser = argparse.ArgumentParser(description='Google Drive sync helper')
    sub = parser.add_subparsers(dest='command', required=True)

    login_p = sub.add_parser('login', help='Eenmalige browser-login')
    login_p.add_argument('--credentials', required=True, help='Pad naar credentials JSON')
    login_p.add_argument('--token', required=True, help='Pad waar token opgeslagen wordt')

    upload_p = sub.add_parser('upload', help='Legacy upload (top-level files only)')
    upload_p.add_argument('--folder', required=True, help='Lokale map om te uploaden')
    upload_p.add_argument('--drive-folder', required=True, help='Naam van Drive-map')
    upload_p.add_argument('--token', required=True, help='Pad naar token-bestand')
    upload_p.add_argument('--extensions', nargs='+', default=['.xlsx'])

    down_p = sub.add_parser('sync-down', help='Mirror Drive map naar lokale map')
    down_p.add_argument('--folder', required=True, help='Lokale map')
    down_p.add_argument('--drive-folder', required=True, help='Naam van Drive-map')
    down_p.add_argument('--token', required=True, help='Pad naar token-bestand')

    up_p = sub.add_parser('sync-up', help='Mirror lokale map naar Drive map')
    up_p.add_argument('--folder', required=True, help='Lokale map')
    up_p.add_argument('--drive-folder', required=True, help='Naam van Drive-map')
    up_p.add_argument('--token', required=True, help='Pad naar token-bestand')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    if args.command == 'login':
        first_login(args.credentials, args.token)
    elif args.command == 'upload':
        upload_folder_to_drive(
            local_folder=args.folder,
            drive_folder_name=args.drive_folder,
            token_path=args.token,
            file_extensions=tuple(args.extensions),
        )
    elif args.command == 'sync-down':
        ok = sync_drive_to_local(
            local_folder=args.folder,
            drive_folder_name=args.drive_folder,
            token_path=args.token,
        )
        if not ok:
            raise SystemExit(1)
    elif args.command == 'sync-up':
        ok = sync_local_to_drive(
            local_folder=args.folder,
            drive_folder_name=args.drive_folder,
            token_path=args.token,
        )
        if not ok:
            raise SystemExit(1)


if __name__ == '__main__':
    _main()
