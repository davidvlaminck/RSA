"""Small helper to atomically stage summary updates for later aggregation.

Usage:
  from outputs.summary_stager import stage_summary_update
  stage_summary_update(payload_dict, staged_dir='RSA_OneDrive/staged_summaries')

This writes an atomic JSON file and returns the final path.
"""
from __future__ import annotations

import json
import uuid
import time
from pathlib import Path
import logging
from typing import Dict, Any


def _ensure_dirs(staged_dir: Path):
    staged_dir.mkdir(parents=True, exist_ok=True)
    (staged_dir / 'processing').mkdir(parents=True, exist_ok=True)
    (staged_dir / 'processed').mkdir(parents=True, exist_ok=True)
    (staged_dir / 'failed').mkdir(parents=True, exist_ok=True)


logger = logging.getLogger(__name__)


def _validate_payload(payload: Dict[str, Any]) -> None:
    if 'operation' not in payload:
        raise ValueError('payload missing operation')
    op = payload['operation']
    if op not in ('append_row', 'write_cell', 'increment_cell'):
        raise ValueError(f'unsupported operation: {op}')
    if 'excel_filename' not in payload and 'spreadsheet_id' not in payload:
        raise ValueError('payload must include excel_filename or spreadsheet_id')
    if 'sheet' not in payload:
        raise ValueError('payload missing sheet')


def stage_summary_update(payload: Dict[str, Any], staged_dir: str | Path = 'RSA_OneDrive/staged_summaries') -> Path:
    """Atomically write payload to a staged json file.

    Returns the final path to the staged file (Path ending with .json).
    """
    staged_dir = Path(staged_dir)
    # If a relative staged_dir is provided, resolve it against the repository root so
    # all code paths consistently write into ProjectRoot/RSA_OneDrive when a
    # relative path is used. This prevents child processes or different cwd's from
    # creating staged files in unexpected locations.
    if not staged_dir.is_absolute():
        repo_root = Path(__file__).resolve().parents[1]
        staged_dir = (repo_root / staged_dir).resolve()
    _ensure_dirs(staged_dir)

    # shallow validate
    _validate_payload(payload)

    ts = time.strftime('%Y%m%dT%H%M%S')
    uid = uuid.uuid4().hex
    filename = f"{ts}_{payload.get('operation')}_{payload.get('meta', {}).get('report','unknown')}_{uid}.json"
    tmp = staged_dir / f"{filename}.tmp"
    final = staged_dir / filename

    # write tmp and then rename
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False)
        f.flush()
        # optional: os.fsync(f.fileno())  # not strictly needed
    tmp.replace(final)
    try:
        logger.info('Staged summary payload to %s (staged_dir=%s)', str(final), str(staged_dir))
    except Exception:
        pass
    return final


# small CLI for quick manual staging (not required, but convenient)
if __name__ == '__main__':
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument('--staged-dir', default='RSA_OneDrive/staged_summaries')
    p.add_argument('--file', help='path to json payload file to stage (reads from disk)')
    args = p.parse_args()
    if not args.file:
        print('Usage: python -m outputs.summary_stager --file payload.json')
        sys.exit(2)
    with open(args.file, 'r', encoding='utf-8') as f:
        payload = json.load(f)
    path = stage_summary_update(payload, staged_dir=args.staged_dir)
    print('Staged to', path)

