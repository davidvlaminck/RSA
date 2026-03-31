"""Google Drive upload helper.

Gebruik:
    1. Eenmalig inloggen via browser:
       python -m scripts.ops.gdrive_upload login \
           --credentials ~/Documenten/AWV/resources/gdrive_oauth_credentials.json \
           --token      ~/Documenten/AWV/resources/gdrive_token.pkl

    2. Upload (automatisch aangeroepen na elke run, of handmatig):
       python -m scripts.ops.gdrive_upload upload \
           --folder /path/to/RSA_OneDrive \
           --drive-folder RSA_Reports \
           --token ~/Documenten/AWV/resources/gdrive_token.pkl

Token-levensduur:
    De access token vervalt na 1 uur maar wordt automatisch ververst door de library.
    De refresh token vervalt nooit, mits de OAuth consent screen op "In production"
    staat in Google Cloud Console (zie README).
"""
from __future__ import annotations

import pickle
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Enkel toegang tot bestanden die door deze app zijn aangemaakt/geüpload.
# Gebruik 'drive' voor toegang tot alle bestanden.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


# ---------------------------------------------------------------------------
# Eenmalige login
# ---------------------------------------------------------------------------

def first_login(credentials_json_path: str, token_path: str) -> None:
    """Eenmalige browser-login. Slaat token op voor toekomstig gebruik.

    Args:
        credentials_json_path: Pad naar het OAuth2 credentials JSON-bestand
                               (gedownload van Google Cloud Console).
        token_path: Pad waar het token opgeslagen wordt (bv. gdrive_token.pkl).
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(credentials_json_path, SCOPES)
    creds = flow.run_local_server(port=0)  # opent browser

    token_file = Path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'wb') as f:
        pickle.dump(creds, f)

    logging.info(f"Token opgeslagen: {token_path}")
    print(f"✓ Ingelogd. Token opgeslagen op: {token_path}")


# ---------------------------------------------------------------------------
# Interne helpers
# ---------------------------------------------------------------------------

def _load_credentials(token_path: str) -> Credentials:
    """Laad token en ververs automatisch als verlopen."""
    with open(token_path, 'rb') as f:
        creds: Credentials = pickle.load(f)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # sla ververste token op
        with open(token_path, 'wb') as f:
            pickle.dump(creds, f)

    return creds


def _get_or_create_folder(service, folder_name: str) -> str:
    """Geeft het Drive folder-ID terug; maakt de map aan als die nog niet bestaat."""
    results = service.files().list(
        q=(
            f"name='{folder_name}' "
            f"and mimeType='application/vnd.google-apps.folder' "
            f"and trashed=false"
        ),
        fields="files(id, name)",
    ).execute()

    folders = results.get('files', [])
    if folders:
        return folders[0]['id']

    folder = service.files().create(
        body={'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'},
        fields='id',
    ).execute()
    return folder['id']


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_folder_to_drive(
    local_folder: str,
    drive_folder_name: str,
    token_path: str,
    file_extensions: tuple[str, ...] = ('.xlsx',),
) -> None:
    """Upload bestanden uit local_folder naar een Google Drive map.

    Bestaande bestanden worden overschreven (update), nieuwe worden aangemaakt.
    Subdirectories worden overgeslagen.

    Args:
        local_folder:       Lokaal pad met te uploaden bestanden.
        drive_folder_name:  Naam van de Drive-map (wordt aangemaakt indien nodig).
        token_path:         Pad naar het token-bestand (aangemaakt door first_login()).
        file_extensions:    Alleen bestanden met deze extensies uploaden. Standaard .xlsx.
    """
    token_file = Path(token_path)
    if not token_file.exists():
        logging.warning(
            f"Drive token niet gevonden: {token_path} — upload overgeslagen.\n"
            f"Voer eerst 'python -m scripts.ops.gdrive_upload login' uit."
        )
        return

    try:
        creds = _load_credentials(token_path)
        service = build('drive', 'v3', credentials=creds)
        folder_id = _get_or_create_folder(service, drive_folder_name)
    except Exception as e:
        logging.error(f"Kon geen verbinding maken met Google Drive: {e}")
        return

    local_path = Path(local_folder)
    uploaded = updated = errors = 0

    for filepath in sorted(local_path.iterdir()):
        if not filepath.is_file():
            continue
        if file_extensions and filepath.suffix.lower() not in file_extensions:
            continue

        try:
            existing = service.files().list(
                q=f"name='{filepath.name}' and '{folder_id}' in parents and trashed=false",
                fields="files(id)",
            ).execute().get('files', [])

            media = MediaFileUpload(str(filepath), resumable=True)

            if existing:
                service.files().update(
                    fileId=existing[0]['id'],
                    media_body=media,
                ).execute()
                logging.info(f"Drive ↑ updated: {filepath.name}")
                updated += 1
            else:
                service.files().create(
                    body={'name': filepath.name, 'parents': [folder_id]},
                    media_body=media,
                ).execute()
                logging.info(f"Drive + uploaded: {filepath.name}")
                uploaded += 1

        except Exception as e:
            logging.error(f"Drive upload mislukt voor {filepath.name}: {e}")
            errors += 1

    logging.info(
        f"Drive upload klaar → '{drive_folder_name}': "
        f"{uploaded} nieuw, {updated} bijgewerkt, {errors} fouten"
    )


# ---------------------------------------------------------------------------
# CLI (voor eerste login en handmatige upload)
# ---------------------------------------------------------------------------

def _main():
    import argparse

    parser = argparse.ArgumentParser(description='Google Drive upload helper')
    sub = parser.add_subparsers(dest='command', required=True)

    login_p = sub.add_parser('login', help='Eenmalige browser-login')
    login_p.add_argument('--credentials', required=True, help='Pad naar credentials JSON')
    login_p.add_argument('--token', required=True, help='Pad waar token opgeslagen wordt')

    upload_p = sub.add_parser('upload', help='Upload map naar Drive')
    upload_p.add_argument('--folder', required=True, help='Lokale map om te uploaden')
    upload_p.add_argument('--drive-folder', required=True, help='Naam van Drive-map')
    upload_p.add_argument('--token', required=True, help='Pad naar token-bestand')
    upload_p.add_argument('--extensions', nargs='+', default=['.xlsx'],
                          help='Te uploaden extensies (default: .xlsx)')

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


if __name__ == '__main__':
    _main()

