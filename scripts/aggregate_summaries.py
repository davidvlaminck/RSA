"""Aggregator for staged summary JSON files.

Scans a staging directory, claims files (moves to processing/), applies operations using ExcelOutput,
and moves processed files to processed/ or failed/.

Usage (dry-run):
  python scripts/aggregate_summaries.py --staged-dir RSA_OneDrive/staged_summaries --dry-run

Usage (real run):
  python scripts/aggregate_summaries.py --staged-dir RSA_OneDrive/staged_summaries --output-dir RSA_OneDrive --limit 100
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

from outputs.excel import ExcelOutput
from outputs.summary_stager import _ensure_dirs

logging.basicConfig(level=logging.INFO, format='[AGG] %(asctime)s %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def apply_payload(excel: ExcelOutput, payload: Dict[str, Any], output_dir: Path) -> None:
    op = payload['operation']
    fname = payload.get('excel_filename') or payload.get('spreadsheet_id')
    sheet = payload['sheet']

    # resolve workbook path using the ExcelOutput resolver (output_dir used implicitly)
    wb_path = excel._resolve_workbook_path(fname)

    if op == 'append_row':
        row = payload['row']
        # append by reading existing rows and writing back with new appended row via write_data_to_sheet
        existing = excel.read_data_from_sheet(str(wb_path), sheet) or []
        # Preserve header: if sheet has header, insert new row after header (index 0 -> header)
        # Determine if first row looks like header (simple heuristic: values are strings and not UUIDs)
        if len(existing) > 0:
            # insert after header: keep existing[0] as header, new row becomes position 1
            combined = [existing[0]] + [row] + existing[1:]
        else:
            combined = [row]
        excel.write_data_to_sheet(wb_path, sheet, combined, overwrite=True)

    elif op == 'write_cell':
        cell = payload['cell']
        value = payload['value']
        # If value is a list, write horizontally across columns starting at `cell`.
        if isinstance(value, list):
            # compute start column and row
            from outputs.sheets_cell import SheetsCell
            sc = SheetsCell(cell)
            col_index = sc._column_int
            row_index = sc._row
            # write each element to successive columns
            for i, v in enumerate(value):
                target_col = SheetsCell._convert_number_to_column(col_index + i)
                target_cell = f"{target_col}{row_index}"
                excel.write_single_cell(wb_path, sheet, target_cell, v)
        else:
            # scalar
            excel.write_single_cell(wb_path, sheet, cell, value)

    elif op == 'increment_cell':
        cell = payload['cell']
        delta = int(payload.get('delta', 1))
        excel.update_row_by_adding_number(wb_path, sheet, cell, delta)

    else:
        raise ValueError(f'Unknown operation: {op}')


def process_once(staged_dir: Path, output_dir: Path, limit: int = 100, dry_run: bool = True) -> int:
    _ensure_dirs(staged_dir)
    files = sorted([p for p in staged_dir.iterdir() if p.is_file() and p.suffix == '.json'])
    if not files:
        logger.info('No staged files found in %s', staged_dir)
        return 0

    excel = ExcelOutput(output_dir=str(output_dir))

    processed = 0
    for f in files[:limit]:
        try:
            processing = staged_dir / 'processing' / f.name
            f.replace(processing)
            logger.info('Processing %s', processing)
            with open(processing, 'r', encoding='utf-8') as fh:
                payload = json.load(fh)

            if dry_run:
                logger.info('Dry-run: would apply %s', payload)
                # move to processed for dry-run just to simulate
                processed_path = staged_dir / 'processed' / processing.name
                processing.replace(processed_path)
                logger.info('Dry-run: moved to processed %s', processed_path)
            else:
                apply_payload(excel, payload, output_dir)
                processed_path = staged_dir / 'processed' / processing.name
                processing.replace(processed_path)
                logger.info('Applied and moved to processed %s', processed_path)

            processed += 1

        except Exception as e:
            logger.exception('Failed to process %s: %s', f, e)
            # move to failed
            try:
                failed_path = staged_dir / 'failed' / f.name
                f.replace(failed_path)
            except Exception:
                logger.exception('Failed to move to failed for %s', f)

    return processed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--staged-dir', default='RSA_OneDrive/staged_summaries')
    p.add_argument('--output-dir', default='RSA_OneDrive')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    staged_dir = Path(args.staged_dir)
    output_dir = Path(args.output_dir)

    logger.info('Scanning staged dir %s', staged_dir)
    n = process_once(staged_dir, output_dir, limit=args.limit, dry_run=args.dry_run)
    logger.info('Processed %d staged files', n)


if __name__ == '__main__':
    main()

