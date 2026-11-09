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
uv run python -m scripts.ops.bootstrap_bucket_layout --output-dir RSA_OneDrive
```

`bootstrap_bucket_layout` is the one-shot repair script for a reset `RSA_OneDrive`: it creates the bucket folders, moves existing report workbooks into the right bucket, and refreshes the summary hyperlinks.
## Daily SharePoint Flow

`main.py` now runs with a daily sync gate mirroring to/from the SharePoint `AIMData` library:
- after `01:00:00`: mirror download from the SharePoint `RSA` folder to local `RSA_OneDrive`
- report window starts based on `settings.time` (for example around `06:00`)
- after reports: mirror upload local `RSA_OneDrive` back to SharePoint
- run log is appended to `RSA_OneDrive/logs/run_YYYYMMDD.log` and uploaded too
- report files are written into 100-report buckets under `RSA_OneDrive/<bucket>/`
- summary links in `Overzicht` and mail links use the same canonical SharePoint URL as the file on disk

Credentials are sourced at runtime from environment variables (set by the operator before running; do not commit secrets):
- `SHAREPOINT_CLIENT_ID`
- `SHAREPOINT_TENANT_ID`
- `SHAREPOINT_SITE_URL`
- `SHAREPOINT_CLIENT_SECRET`

```json
{
  "sharepoint_sync": {
    "enabled": true,
    "sync_after": "02:00:00",
    "poll_after": "01:00:00",
    "poll_deadline": "06:00:00",
    "sharepoint_folder": "RSA",
    "local_folder": "./RSA_OneDrive"
  }
}
```

The remote folder is the `RSA` folder inside the `AIMData` document library. No token file is required.

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

