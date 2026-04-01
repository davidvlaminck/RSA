#!/usr/bin/env python3
"""Google Drive token bootstrap + folder access check.

Gebruik:
  uv run python -m scripts.setup_gdrive_token \
    --credentials /path/to/oauth_client.json \
    --token /path/to/gdrive_token.pkl \
    --drive-folder RSA
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

FOLDER_MIME = 'application/vnd.google-apps.folder'
SCOPES = ['https://www.googleapis.com/auth/drive']
DEFAULT_SETTINGS = str(Path(__file__).resolve().parents[1] / 'settings_sample.json')
DEFAULT_CREDENTIALS = '/home/davidlinux/Documenten/AWV/resources/client_secret_RSA-API.json'
DEFAULT_TOKEN = '/home/davidlinux/Documenten/AWV/resources/gdrive_token.pkl'
DEFAULT_DRIVE_FOLDER = 'RSA'


def _load_settings(settings_path: str) -> dict:
    path = Path(settings_path)
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def _save_settings(settings_path: str, settings: dict) -> None:
    with open(settings_path, 'w', encoding='utf-8') as fh:
        json.dump(settings, fh, indent=4)


def _resolve_config(settings: dict) -> tuple[str, str, str]:
    drive_sync = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
    google_api = settings.get('google_api', {}) if isinstance(settings, dict) else {}

    credentials_path = (
        drive_sync.get('credentials_path')
        or google_api.get('credentials_path')
        or DEFAULT_CREDENTIALS
    )
    token_path = drive_sync.get('token_path') or DEFAULT_TOKEN
    drive_folder = drive_sync.get('drive_folder') or DEFAULT_DRIVE_FOLDER
    return credentials_path, token_path, drive_folder


def _load_credentials(token_path: str):
    from google.auth.transport.requests import Request

    with open(token_path, 'rb') as fh:
        creds = pickle.load(fh)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'wb') as fh:
            pickle.dump(creds, fh)

    return creds


def create_token(credentials_json_path: str, token_path: str) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(credentials_json_path, SCOPES)
    creds = flow.run_local_server(port=0)

    token_file = Path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'wb') as fh:
        pickle.dump(creds, fh)


def _safe_name(name: str) -> str:
    return name.replace("'", "\\'")


def check_folder_access(token_path: str, drive_folder: str, create_if_missing: bool = True) -> tuple[bool, str]:
    from googleapiclient.discovery import build

    creds = _load_credentials(token_path)
    service = build('drive', 'v3', credentials=creds)

    query = (
        f"name='{_safe_name(drive_folder)}' "
        f"and mimeType='{FOLDER_MIME}' "
        "and trashed=false"
    )

    result = service.files().list(q=query, fields='files(id, name)', pageSize=1).execute()
    found = result.get('files', [])
    if found:
        return True, found[0]['id']

    if not create_if_missing:
        return False, ''

    created = service.files().create(
        body={'name': drive_folder, 'mimeType': FOLDER_MIME},
        fields='id',
    ).execute()
    return True, created['id']


def main() -> int:
    parser = argparse.ArgumentParser(description='Maak Drive token aan en check maptoegang')
    parser.add_argument('--settings', default=DEFAULT_SETTINGS, help='Pad naar settings.json (default: settings_sample.json)')
    parser.add_argument('--credentials', default=None, help='Override OAuth client credentials JSON')
    parser.add_argument('--token', default=None, help='Override token pad (.pkl)')
    parser.add_argument('--drive-folder', default=None, help='Override Drive-mapnaam')
    parser.add_argument('--no-create-folder', action='store_true', help='Faalt als map niet bestaat')
    parser.add_argument('--force-login', action='store_true', help='Forceer nieuwe browser login ook als token al bestaat')
    parser.add_argument('--write-settings', action='store_true', help='Sla overrides op in settings drive_sync')
    parser.add_argument('--dry-run', action='store_true', help='Toon enkel resolved configuratie')
    args = parser.parse_args()

    settings = _load_settings(args.settings)
    cfg_credentials, cfg_token, cfg_folder = _resolve_config(settings)

    credentials = args.credentials or cfg_credentials
    token = args.token or cfg_token
    drive_folder = args.drive_folder or cfg_folder

    print('Using setup config:')
    print(f'  settings     : {args.settings}')
    print(f'  credentials  : {credentials}')
    print(f'  token        : {token}')
    print(f'  drive_folder : {drive_folder}')

    if args.dry_run:
        return 0

    token_path = Path(token)
    if token_path.exists() and not args.force_login:
        print(f'Token bestaat al, login overgeslagen: {token}')
    else:
        credentials_path = Path(credentials)
        if not credentials_path.exists():
            print('ERROR: OAuth client credentials bestand niet gevonden.')
            print(f'  verwacht pad: {credentials}')
            return 1
        try:
            create_token(credentials, token)
            print(f'Token aangemaakt: {token}')
        except Exception as exc:
            print(f'ERROR: token aanmaken mislukt: {exc}')
            return 1

    try:
        ok, folder_id = check_folder_access(
            token_path=token,
            drive_folder=drive_folder,
            create_if_missing=not args.no_create_folder,
        )
    except Exception as exc:
        print(f'ERROR: Drive toegangstest mislukt: {exc}')
        return 2

    if not ok:
        print(f"ERROR: map '{drive_folder}' niet gevonden en niet aangemaakt")
        return 3

    print(f"Drive map '{drive_folder}' is toegankelijk (id={folder_id})")

    if args.write_settings:
        if not isinstance(settings, dict):
            settings = {}
        settings.setdefault('google_api', {})
        settings['google_api']['credentials_path'] = credentials
        settings.setdefault('drive_sync', {})
        settings['drive_sync']['token_path'] = token
        settings['drive_sync']['drive_folder'] = drive_folder
        settings['drive_sync']['credentials_path'] = credentials
        _save_settings(args.settings, settings)
        print(f'Settings bijgewerkt: {args.settings}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())

