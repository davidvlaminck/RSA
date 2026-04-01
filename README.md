# RSA Report Service

Reporting service for AWV infrastructure data.

## Quick Start (uv)

```bash
uv sync
uv sync --extra dev
uv run python run_single_report.py --once --report Report0002
```

Alternative (`uv pip` with `pyproject.toml`):

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[dev]"
```

Common commands:

```bash
uv run python main.py
uv run python main_selection_list.py --parallel
uv run pytest
```

## Daily Google Drive Flow

`main.py` now runs with a daily sync gate:
- after `01:00:00`: mirror download from Drive folder to local `RSA_OneDrive`
- report window starts based on `settings.time` (for example around `06:00`)
- after reports: mirror upload local `RSA_OneDrive` back to Drive
- run log is appended to `RSA_OneDrive/logs/run_YYYYMMDD.log` and uploaded too

Token bootstrap + mapcheck (`RSA`):

```bash
uv run python -m scripts.setup_gdrive_token \
  --credentials /path/to/oauth_client.json \
  --token /path/to/gdrive_token.pkl \
  --drive-folder RSA
```

PyCharm one-click setup (zonder args):
- Run `scripts/setup_gdrive_token.py` met Play.
- Script leest standaard `settings_sample.json`.
- Voeg `--write-settings` toe om gebruikte paden terug in settings op te slaan.

```bash
uv run python -m scripts.setup_gdrive_token --write-settings
```

OAuth bootstrap (one-time):

```bash
uv run python -m scripts.ops.gdrive_upload login \
  --credentials /path/to/oauth_client.json \
  --token /path/to/gdrive_token.pkl
```

Manual sync commands:

```bash
uv run python -m scripts.ops.gdrive_upload sync-down --folder RSA_OneDrive --drive-folder RSA --token /path/to/gdrive_token.pkl
uv run python -m scripts.ops.gdrive_upload sync-up --folder RSA_OneDrive --drive-folder RSA --token /path/to/gdrive_token.pkl
```

One-shot pre-sync test (without running reports):

```bash
uv run python -m scripts.ops.dry_sync_test --settings settings_sample.json --dry-run
uv run python -m scripts.ops.dry_sync_test --settings settings_sample.json --token /real/path/gdrive_token.pkl
```

### Persoonlijke Google Drive setup

Gebruik voor een persoonlijke Google Drive exact dezelfde OAuth-flow als voor een werkaccount. Je hebt eerst een OAuth client JSON nodig (`credentials_path`), daarna maakt het setup-script een user token aan (`token_path`).

1. Maak een vaste map voor de bestanden:

```bash
mkdir -p /home/davidlinux/Documenten/AWV/resources
```

2. Open Google Cloud Console en doe het volgende:
   - maak een nieuw project
   - activeer **Google Drive API**
   - ga naar **APIs & Services** → **OAuth consent screen**
   - ga naar **Audience** en controleer **Publishing status**
   - zet de app op **In production/Published** als je met niet-testgebruikers wil inloggen
   - als tijdelijke fallback: voeg je Google-account toe onder **Test users** zolang status op **Testing** staat
   - kies **External**
   - vul minimaal app name + jouw e-mailadres in
   - ga naar **Credentials** → **Create Credentials** → **OAuth client ID**
   - kies **Desktop app**
   - download het JSON-bestand

3. Sla dat JSON-bestand lokaal op, bijvoorbeeld als:

```bash
/home/davidlinux/Documenten/AWV/resources/gdrive_oauth_credentials.json
```

4. Run daarna in PyCharm gewoon `scripts/setup_gdrive_token.py` met Play, of via terminal:

```bash
uv run python -m scripts.setup_gdrive_token \
  --credentials /home/davidlinux/Documenten/AWV/resources/gdrive_oauth_credentials.json \
  --token /home/davidlinux/Documenten/AWV/resources/gdrive_token.pkl \
  --drive-folder RSA \
  --write-settings
```

5. Er opent een browser. Log in met je persoonlijke Google account en geef toestemming.

6. Na succesvolle login:
   - wordt `gdrive_token.pkl` aangemaakt
   - test het script of map `RSA` bereikbaar is
   - schrijft `--write-settings` de gebruikte paden terug naar je settingsbestand

7. Controleer daarna deze velden in je settings:

```json
{
  "google_api": {
    "credentials_path": "/home/davidlinux/Documenten/AWV/resources/gdrive_oauth_credentials.json"
  },
  "drive_sync": {
    "credentials_path": "/home/davidlinux/Documenten/AWV/resources/gdrive_oauth_credentials.json",
    "token_path": "/home/davidlinux/Documenten/AWV/resources/gdrive_token.pkl",
    "drive_folder": "RSA",
    "local_folder": "./RSA_OneDrive"
  }
}
```

Verschil tussen beide paden:
- `credentials_path`: het OAuth client JSON-bestand dat je downloadt uit Google Cloud Console
- `token_path`: het login-token dat het Python-script lokaal aanmaakt na browser-login

## Documentation

- `spec.md` - project summary and scope
- `analysis.md` - requirements and acceptance criteria
- `implementation_details.md` - developer implementation details
- `architecture.md` - runtime architecture and execution flow
- `DOCUMENTATION_GUIDE.md` - reading guide by role/use case

Specialist docs:
- `docs/timestamps.md` - timestamp semantics and troubleshooting
- `docs/excel_output_spec.md` - Excel writer contract
- `AQL/readMe.md` - AQL query folder notes
- `ArchivedReports/README.md` - archived report index

## Configuration

Sample settings files:
- `settings_sample.json`
- `settings_parallel_example.json`

For current configuration behavior, see `implementation_details.md` and `SettingsManager.py`.

