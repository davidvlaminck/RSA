#!/usr/bin/env python3
"""Simple utility to append a file-change entry into a log file.

Usage:
  python scripts/file_change_log.py --action CREATED --path /full/path/to/file

This is intentionally tiny and invoked by other scripts whenever they create or modify files.
The log file is at .gitignored path: scripts/file_changes.log
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / 'file_changes.log'


def append_entry(action: str, path: str):
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"{ts}\t{action}\t{path}\n"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'a', encoding='utf-8') as fh:
        fh.write(entry)
    print(entry, end='')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--action', required=True, choices=['CREATED', 'MODIFIED', 'DELETED'])
    p.add_argument('--path', required=True)
    args = p.parse_args()
    append_entry(args.action, args.path)
