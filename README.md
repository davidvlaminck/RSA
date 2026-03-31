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
uv run python scripts/ops/run_one_report_and_mail_archive.py --report Report0002
uv run pytest
```

Main entrypoints:
- `main.py`
- `run_single_report.py`
- `main_selection_list.py`

Archive email:
- `main.py` now zips the configured Excel output directory after a full run and mails it to `david.vlaminck@mow.vlaanderen.be` using `smtp_options`.
- For a focused test flow, use `scripts/ops/run_one_report_and_mail_archive.py`.

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

