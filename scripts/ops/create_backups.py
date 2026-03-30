#!/usr/bin/env python3
"""Create timestamped backups of Excel files in RSA_OneDrive.

This is an explicit utility that must be called to create backups. No scripts create backups automatically.

Usage:
  # Backup a single file by exact filename (relative to RSA_OneDrive)
  python3 scripts/ops/create_backups.py --file "[RSA] TLCfipoorten hebben een sturingsrelatie naar een Verkeersregelaar.xlsx"

  # Backup all report files matching a pattern
  python3 scripts/ops/create_backups.py --glob "[RSA]*TLC*"

  # Dry-run
  python3 scripts/ops/create_backups.py --glob "[RSA]*" --dry-run

"""
from pathlib import Path
import argparse
import logging
import sys

# Ensure project root is on sys.path so imports work when running script directly
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# local imports after sys.path adjustment
try:
    from outputs.excel import ExcelOutput
except Exception as exc:
    ExcelOutput = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

DEFAULT_DIR = Path.cwd() / 'RSA_OneDrive'

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Create timestamped backups for RSA Excel files')
parser.add_argument('--file', help='Exact filename inside RSA_OneDrive to backup (e.g. "[RSA] Foo.xlsx")')
parser.add_argument('--glob', help='Glob pattern to match files inside RSA_OneDrive (e.g. "[RSA]*Foo*")')
parser.add_argument('--output-dir', help='RSA_OneDrive dir (default: RSA_OneDrive)', default=None)
parser.add_argument('--dry-run', action='store_true', help='Do not perform backups, only show what would be done')

args = parser.parse_args()

out_dir = Path(args.output_dir) if args.output_dir else DEFAULT_DIR
if not out_dir.exists():
    logger.error('Output dir does not exist: %s', out_dir)
    raise SystemExit(1)

if ExcelOutput is None:
    logger.error('Failed to import ExcelOutput from outputs.excel: %s', _IMPORT_ERROR)
    logger.error('Make sure you run this script with the project root on PYTHONPATH, e.g. `PYTHONPATH=. python3 scripts/create_backups.py ...`')
    raise SystemExit(1)

ex = ExcelOutput(output_dir=str(out_dir))

candidates = []
if args.file:
    p = out_dir / args.file
    if p.exists():
        candidates.append(p)
    else:
        logger.error('File not found: %s', p)
        raise SystemExit(1)
elif args.glob:
    for f in sorted(out_dir.glob(args.glob)):
        if f.is_file():
            candidates.append(f)
else:
    logger.error('Please specify --file or --glob')
    raise SystemExit(1)

logger.info('Found %d files to backup', len(candidates))
for c in candidates:
    logger.info(' - %s', c.name)

if args.dry_run:
    logger.info('Dry-run; no backups created')
    raise SystemExit(0)

for c in candidates:
    backup = ex.backup_file(c)
    logger.info('Backed up %s -> %s', c.name, backup.name)

logger.info('Done')

