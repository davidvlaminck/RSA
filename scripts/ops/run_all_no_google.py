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

DEFAULT_SETTINGS = str(repo_root / 'settings_sample.json')


def prepare_temp_settings(orig_settings_path: str | None, excel_output_dir: str | None = None, query_timeout_seconds: int | None = None, arango_request_timeout_seconds: int | None = None, max_concurrent: int | None = None) -> str:
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

    drive_cfg = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
    excel_cfg = settings.get('output', {}).get('excel', {}) if isinstance(settings, dict) else {}
    out_dir = excel_output_dir or drive_cfg.get('local_folder') or excel_cfg.get('output_dir')
    if out_dir is None:
        out_dir = str(repo_root / 'RSA_OneDrive')
    settings['output']['excel']['output_dir'] = out_dir

    settings['force_excel'] = True
    settings['google_api'] = {}

    if 'report_execution' not in settings or not isinstance(settings['report_execution'], dict):
        settings['report_execution'] = {}
    if query_timeout_seconds is not None:
        settings['report_execution']['query_timeout_seconds'] = int(query_timeout_seconds)
    if arango_request_timeout_seconds is not None:
        settings['report_execution']['arango_request_timeout_seconds'] = int(arango_request_timeout_seconds)
    if max_concurrent is not None:
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
    p.add_argument('--query-timeout', type=int, default=60, help='Query timeout per report in seconds (sets report_execution.query_timeout_seconds)')
    p.add_argument('--arango-request-timeout', type=int, default=180, help='ArangoDB request timeout in seconds (sets report_execution.arango_request_timeout_seconds)')
    p.add_argument('--max-concurrent', type=int, default=2, help='Maximum number of concurrent pipelines (sets report_execution.max_concurrent)')
    p.add_argument('--limit', type=int, default=1000)
    args = p.parse_args()

    chosen_output = args.folder_path or args.output_dir

    tmp_settings = prepare_temp_settings(
        args.settings,
        excel_output_dir=chosen_output,
        query_timeout_seconds=args.query_timeout,
        arango_request_timeout_seconds=args.arango_request_timeout,
        max_concurrent=args.max_concurrent,
    )
    print(f'Using temporary settings: {tmp_settings}')

    try:
        instances = discover_and_instantiate_reports()
        report_names = [type(i).__name__ for i in instances] if instances else []

        if not report_names:
            print('No reports discovered under Reports/. Nothing to run.')
            return

        if chosen_output:
            out_dir = Path(chosen_output)
        else:
            with open(args.settings, 'r', encoding='utf-8') as fh:
                settings = json.load(fh)
            drive_cfg = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
            excel_cfg = settings.get('output', {}).get('excel', {}) if isinstance(settings, dict) else {}
            out_dir = Path(drive_cfg.get('local_folder') or excel_cfg.get('output_dir') or (repo_root / 'RSA_OneDrive'))
        try:
            SingleExcelWriter.init(output_dir=str(out_dir))
            print('Initialized SingleExcelWriter with dir:', out_dir)
        except Exception:
            print('Warning: failed to init SingleExcelWriter in driver process')

        try:
            with open(tmp_settings, 'r', encoding='utf-8') as fh:
                tmp_settings_dict = json.load(fh)
        except Exception:
            tmp_settings_dict = {}

        rc = run_pipelines_by_datasource(report_names, tmp_settings_dict, tmp_settings, stream_output=True)
        if rc is not None and rc != 0:
            print('One or more pipelines failed (rc=', rc, ')')
        else:
            print('Pipelines finished (rc=', rc, ')')

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



