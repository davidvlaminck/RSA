#!/usr/bin/env python3
"""
Run a fixed set of reports in parallel while disabling Google Sheets for the run.

This script:
- Loads an existing settings.json (defaults to the project's default)
- Produces a temporary settings file where Google API credentials are removed and Excel output
  is forced (using settings['force_excel']=true)
- Calls the shared runner `run_selection` with `force_parallel=True` so each datasource pipeline
  runs in its own worker subprocess

Usage:
    python scripts/run_reports_no_google.py --settings /path/to/settings.json

This avoids needing to monkeypatch SingleSheetsWrapper in-process because worker subprocesses
read the modified temp settings and therefore will not attempt Google initialization.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import os
from pathlib import Path
import shutil
import sys

# Ensure repository root is on sys.path so `lib` package imports work when this script
# is executed directly or via subprocess from a different working dir.
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.reports.selection_runner import run_selection


DEFAULT_SETTINGS = r"/home/davidlinux/Documenten/AWV/resources/settings_RSA.json"
DEFAULT_REPORTS = [
    "Report0002",
    "Report0004",
    "Report0030",
    "Report0048",
]


def prepare_temp_settings(orig_settings_path: str | None, excel_output_dir: str | None = None) -> str:
    """Return path to a temp settings JSON file with Google disabled and Excel forced.

    - If orig_settings_path is provided and exists, load it; otherwise start from minimal defaults.
    - Remove/clear `google_api` so workers won't initialize Google Sheets wrapper.
    - Ensure output.excel.output_dir is set so Excel writer can initialize.
    - Set force_excel flag so factories.make_output will prefer Excel.
    """
    settings = {}
    if orig_settings_path:
        try:
            with open(orig_settings_path, 'r', encoding='utf-8') as fh:
                settings = json.load(fh)
        except Exception:
            settings = {}

    # Ensure top-level structures exist
    if 'output' not in settings or not isinstance(settings['output'], dict):
        settings['output'] = {}
    if 'excel' not in settings['output'] or not isinstance(settings['output']['excel'], dict):
        settings['output']['excel'] = {}

    # Choose output_dir
    out_dir = excel_output_dir or settings['output']['excel'].get('output_dir')
    if out_dir is None:
        # default inside project root
        proj_root = Path(__file__).resolve().parents[1]
        out_dir = str(proj_root / 'RSA_OneDrive')
    settings['output']['excel']['output_dir'] = out_dir

    # Force Excel output for the whole run
    settings['force_excel'] = True

    # Disable Google API credentials so code paths that check for credentials skip initialization
    # (workers check for settings.get('google_api', {}).get('credentials_path'))
    settings['google_api'] = {}

    # Persist the modified settings to a temp file so child workers read the same configuration
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp_path = tmp.name
    with open(tmp_path, 'w', encoding='utf-8') as fh:
        json.dump(settings, fh, indent=2)
    return tmp_path


def main():
    parser = argparse.ArgumentParser(description='Run a set of reports in parallel without Google Sheets')
    parser.add_argument('--settings', help='Path to settings JSON', default=DEFAULT_SETTINGS)
    parser.add_argument('--reports', nargs='+', help='Report names to run', default=DEFAULT_REPORTS)
    parser.add_argument('--output-dir', help='Optional output dir for Excel files (overrides settings)', default=None)
    parser.add_argument('--folder-path', help='Optional Path to RSA_OneDrive folder (preferred over --output-dir)', default=None)

    args = parser.parse_args()

    # Prefer explicit folder-path over output-dir for directing where Excel files are written
    chosen_output = args.folder_path or args.output_dir
    tmp_settings = prepare_temp_settings(args.settings, excel_output_dir=chosen_output)

    try:
        print(f"Using temporary settings: {tmp_settings}")
        # run_selection will read settings from the temp file and we force parallel below
        rc = run_selection(settings_path=tmp_settings, report_names=args.reports, force_parallel=True, stream_output=True)
        if rc != 0:
            print(f"One or more pipelines failed (exit code {rc})")
        else:
            print("All pipelines finished successfully")

        # After reports finished, run aggregator to apply staged summary updates
        try:
            from scripts.aggregate_summaries import process_once
            staged_dir = Path(args.output_dir or Path(tmp_settings).with_suffix('').name)
        except Exception:
            staged_dir = None

        # call aggregator
        # Use folder_path if provided, else output-dir, else default 'RSA_OneDrive' in repo root
        output_dir_choice = Path(args.folder_path or args.output_dir or 'RSA_OneDrive')
        agg_staged = output_dir_choice / 'staged_summaries'
        from scripts.aggregate_summaries import process_once as agg_process_once
        print(f"Running aggregator on staged dir: {agg_staged}")
        applied = agg_process_once(Path(agg_staged), Path(output_dir_choice), limit=100, dry_run=False)
        print(f"Aggregator applied {applied} staged updates")

    finally:
        try:
            os.unlink(tmp_settings)
        except Exception:
            pass


if __name__ == '__main__':
    main()

