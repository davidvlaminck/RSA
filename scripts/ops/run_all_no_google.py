#!/usr/bin/env python3
"""
Run all reports (the ones in Reports/) in parallel without Google Sheets.

This script:
- Loads an existing settings.json (defaults to project's default)
- Produces a temporary settings file where Google API credentials are removed and Excel output
  is forced (using settings['force_excel']=true)
- Discovers all reports under Reports/ and runs them grouped by datasource (parallel)
- Calls the aggregator to apply staged summary updates

Usage:
  python scripts/ops/run_all_no_google.py --settings /path/to/settings.json
"""

from __future__ import annotations

import argparse
import json
import tempfile
import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path so imports work when executed from other cwd
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.reports.instantiator import discover_and_instantiate_reports
from lib.reports.pipeline_runner import run_pipelines_by_datasource
from outputs.excel_wrapper import SingleExcelWriter

DEFAULT_SETTINGS = r"/home/davidlinux/Documenten/AWV/resources/settings_RSA.json"


def prepare_temp_settings(orig_settings_path: str | None, excel_output_dir: str | None = None, timeout_seconds: int | None = None, max_concurrent: int | None = None) -> str:
    settings = {}
    if orig_settings_path:
        try:
            with open(orig_settings_path, 'r', encoding='utf-8') as fh:
                settings = json.load(fh)
        except Exception:
            settings = {}

    if 'output' not in settings or not isinstance(settings['output'], dict):
        settings['output'] = {}
    if 'excel' not in settings['output'] or not isinstance(settings['output']['excel'], dict):
        settings['output']['excel'] = {}

    out_dir = excel_output_dir or settings['output']['excel'].get('output_dir')
    if out_dir is None:
        out_dir = str(repo_root / 'RSA_OneDrive')
    settings['output']['excel']['output_dir'] = out_dir

    # enforce excel output and disable Google API
    settings['force_excel'] = True
    settings['google_api'] = {}

    # allow overriding per-pipeline timeout via CLI
    if timeout_seconds is not None:
        if 'report_execution' not in settings or not isinstance(settings['report_execution'], dict):
            settings['report_execution'] = {}
        settings['report_execution']['timeout_seconds'] = int(timeout_seconds)
    # allow overriding max_concurrent via CLI
    if max_concurrent is not None:
        if 'report_execution' not in settings or not isinstance(settings['report_execution'], dict):
            settings['report_execution'] = {}
        settings['report_execution']['max_concurrent'] = int(max_concurrent)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name
        json.dump(settings, tmp, indent=2)

    return tmp_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--settings', default=DEFAULT_SETTINGS)
    p.add_argument('--output-dir', default=None)
    p.add_argument('--folder-path', default=None)
    # timeout and concurrency controls for pipeline execution
    p.add_argument('--timeout-seconds', type=int, default=1800, help='Timeout for pipelines in seconds (sets report_execution.timeout_seconds)')
    # deprecated alias kept for backward-compatibility
    p.add_argument('--timeout', type=int, default=None, help=argparse.SUPPRESS)
    p.add_argument('--max-concurrent', type=int, default=2, help='Maximum number of concurrent pipelines (sets report_execution.max_concurrent)')
    p.add_argument('--limit', type=int, default=1000)
    args = p.parse_args()

    chosen_output = args.folder_path or args.output_dir

    # Prepare temp settings with Google disabled and Excel forced
    # prefer explicit --timeout-seconds; fall back to deprecated --timeout if provided
    timeout_choice = args.timeout if args.timeout is not None else args.timeout_seconds
    tmp_settings = prepare_temp_settings(
        args.settings, excel_output_dir=chosen_output, timeout_seconds=timeout_choice, max_concurrent=args.max_concurrent
    )
    print(f'Using temporary settings: {tmp_settings}')

    try:
        # Discover reports (instantiate to ensure discovery)
        instances = discover_and_instantiate_reports()
        report_names = [type(i).__name__ for i in instances] if instances else []

        if not report_names:
            print('No reports discovered under Reports/. Nothing to run.')
            return

        # Ensure Excel writer is initialized in this process so aggregator and other helpers can use it
        out_dir = chosen_output or (repo_root / 'RSA_OneDrive')
        out_dir = Path(out_dir)
        try:
            SingleExcelWriter.init(output_dir=str(out_dir))
            print('Initialized SingleExcelWriter with dir:', out_dir)
        except Exception:
            print('Warning: failed to init SingleExcelWriter in driver process')

        # Load the temp settings file into a dict so we can pass settings to the pipeline runner
        try:
            with open(tmp_settings, 'r', encoding='utf-8') as fh:
                tmp_settings_dict = json.load(fh)
        except Exception:
            tmp_settings_dict = {}

        # Run pipelines grouped by datasource using the temp settings file so workers don't init Google
        rc = run_pipelines_by_datasource(report_names, tmp_settings_dict, tmp_settings, stream_output=True)
        if rc is not None and rc != 0:
            print('One or more pipelines failed (rc=', rc, ')')
        else:
            print('Pipelines finished (rc=', rc, ')')

        # Run aggregator to apply staged updates
        from scripts.ops.aggregate_summaries import process_once as agg_process_once
        output_dir_choice = out_dir.resolve()
        staged = output_dir_choice / 'staged_summaries'
        print(f'Running aggregator on staged dir: {staged} (output dir: {output_dir_choice})')
        applied = agg_process_once(staged, output_dir_choice, limit=args.limit, dry_run=False)
        print(f'Aggregator applied {applied} staged updates (output_dir={output_dir_choice})')

    finally:
        try:
            os.unlink(tmp_settings)
        except Exception:
            pass


if __name__ == '__main__':
    main()



