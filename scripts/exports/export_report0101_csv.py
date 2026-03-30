#!/usr/bin/env python3
"""
Export Report0101 (Vplan koppelingen) to CSV using the safe AQL variant (CSV-friendly).

Usage examples:
  # Use settings file (default path or --settings):
  python scripts/exports/export_report0101_csv.py --settings /home/davidlinux/Documenten/AWV/resources/settings_RSA.json --out /tmp/report0101.csv

  # Or override connection parameters directly:
  python scripts/exports/export_report0101_csv.py --host 127.0.0.1 --port 8529 --user myuser --password 'mypw' --database awvinfra --out /tmp/report0101.csv

Notes:
- The script uses the same settings resolution as other scripts: explicit --settings, then RSA_SETTINGS env var, then default path.
- The script executes a read-only AQL on ArangoDB and streams rows to CSV; it does not modify the database.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

DEFAULT_SETTINGS_PATH = Path(os.environ.get('RSA_SETTINGS') or Path.home() / 'Documenten' / 'AWV' / 'resources' / 'settings_RSA.json')


def load_settings(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as fh:
        return json.load(fh)


def resolve_conf(args) -> dict:
    # CLI overrides take precedence
    if args.host and args.port and args.user and args.database:
        return {
            'host': args.host,
            'port': args.port,
            'user': args.user,
            'password': args.password or '',
            'database': args.database
        }
    # otherwise load settings JSON
    settings_path = Path(args.settings) if args.settings else DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    s = load_settings(settings_path)
    dbs = s.get('databases', {})
    conf = dbs.get('ArangoDB') or dbs.get('arangodb')
    if not conf:
        raise KeyError('No ArangoDB configuration found in settings file under databases.ArangoDB')
    return conf


def main() -> int:
    p = argparse.ArgumentParser(description='Export Report0101 as CSV using ArangoDB')
    p.add_argument('--settings', help='Path to settings JSON (optional)', default=None)
    p.add_argument('--host', help='Arango host (overrides settings)')
    p.add_argument('--port', help='Arango port (overrides settings)')
    p.add_argument('--user', help='Arango username (overrides settings)')
    p.add_argument('--password', help='Arango password (overrides settings)')
    p.add_argument('--database', help='Arango database name (overrides settings)')
    p.add_argument('--mode', choices=['safe','debug'], default='safe', help='Which stored query to run (safe for CSV)')
    p.add_argument('--example', action='store_true', help='Run in example mode using in-memory sample rows (no DB)')
    p.add_argument('--out', required=False, default='/tmp/report0101.csv', help='Destination CSV file')

    args = p.parse_args()

    # Example mode: write a small sample CSV without connecting to any DB (useful for testing table layout)
    if args.example:
        sample_rows = [
            {'uuid': '1111', 'installatie': 'instA', 'naampad': 'a/b', 'actief': True, 'toestand': 'in-gebruik'},
            {'uuid': '2222', 'installatie': 'instB', 'naampad': 'c/d', 'actief': True, 'toestand': 'in-gebruik', 'extra': [1,2,3]},
            {'uuid': '3333', 'installatie': 'instC', 'naampad': 'e/f', 'actief': False}
        ]
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # derive header
        header = []
        for r in sample_rows:
            for k in r.keys():
                if k not in header:
                    header.append(k)
        with out_path.open('w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow([str(h) for h in header])
            for r in sample_rows:
                writer.writerow([str(_format_cell(r.get(k, ''))) for k in header])
        print('Wrote example CSV to', out_path)
        return 0

    try:
        conf = resolve_conf(args)
    except Exception as e:
        print('Failed to resolve ArangoDB settings:', e, file=sys.stderr)
        return 2

    # import connector and report module
    try:
        from datasources.arango import SingleArangoConnector
    except Exception as e:
        print('Failed to import SingleArangoConnector:', e, file=sys.stderr)
        return 3

    try:
        # initialize connector
        SingleArangoConnector.init(host=conf.get('host'), port=str(conf.get('port')), user=conf.get('user'), password=conf.get('password'), database=conf.get('database'))
        db = SingleArangoConnector.get_db()
    except Exception as e:
        print('Failed to initialize ArangoDB connection:', repr(e), file=sys.stderr)
        return 4

    # load report module to get the AQL
    try:
        # prefer package import
        try:
            from importlib import import_module
            mod = import_module('Reports.Report0101')
        except Exception:
            # fallback: load by path
            from importlib.machinery import SourceFileLoader
            repo_root = Path(__file__).resolve().parents[2]
            report_path = repo_root / 'Reports' / 'Report0101.py'
            loader = SourceFileLoader('report0101', str(report_path))
            mod = loader.load_module()
    except Exception as e:
        print('Failed to import Reports.Report0101:', e, file=sys.stderr)
        return 5

    # pick query
    if args.mode == 'safe':
        q = getattr(mod, 'aql_safe_query', None)
    else:
        q = getattr(mod, 'aql_debug_query', None)
    if not q:
        print('No appropriate query found in Reports.Report0101 (expected aql_safe_query or aql_debug_query).', file=sys.stderr)
        return 6

    # execute and stream to CSV
    try:
        cursor = db.aql.execute(q)
    except Exception as e:
        print('Failed to execute AQL:', repr(e), file=sys.stderr)
        return 7

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # stream rows: determine header from first row
    try:
        it = iter(cursor)
        first_row = next(it, None)
    except Exception as e:
        print('Failed iterating cursor:', e, file=sys.stderr)
        return 8

    if first_row is None:
        # nothing to write
        out_path.write_text('')
        print('Query returned no rows; wrote empty file at', out_path)
        return 0

    # first-row must be a dict; otherwise serialize it as a single column
    if not isinstance(first_row, dict):
        # write single column 'value'
        with out_path.open('w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(['value'])
            writer.writerow([json.dumps(first_row, ensure_ascii=False)])
            for row in it:
                writer.writerow([json.dumps(row, ensure_ascii=False)])
        print('Wrote CSV to', out_path)
        return 0

    # determine header keys preserving insertion order
    # try to use cursor.keys() if available
    header = []
    try:
        if hasattr(cursor, 'keys'):
            k = cursor.keys()
            if k:
                header = list(k)
    except Exception:
        header = []

    if not header:
        # infer from first row and subsequent rows encountered
        seen = []
        for k in first_row.keys():
            if k not in seen:
                seen.append(k)
        # scan a small prefix of the cursor to collect additional keys without loading too many rows
        prefix = []
        for _ in range(100):
            try:
                r = next(it)
            except StopIteration:
                r = None
            if r is None:
                break
            prefix.append(r)
            if isinstance(r, dict):
                for k in r.keys():
                    if k not in seen:
                        seen.append(k)
        header = seen
        # create a new iterator that includes the prefix rows followed by the rest of cursor
        def chained():
            for r in prefix:
                yield r
            for r in it:
                yield r
        rows_iter = chained()
    else:
        # header known; rows_iter is remaining iterator
        rows_iter = it

    # write CSV
    with out_path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        # ensure header elements are strings
        safe_header = [str(h) for h in header]
        writer.writerow(safe_header)
        # write first row
        row_values = [first_row.get(k, '') for k in header]
        writer.writerow([str(_format_cell(v)) for v in row_values])
        # stream remaining rows
        for r in rows_iter:
            if not isinstance(r, dict):
                writer.writerow([json.dumps(r, ensure_ascii=False)])
                continue
            vals = [r.get(k, '') for k in header]
            writer.writerow([str(_format_cell(v)) for v in vals])

    print('Wrote CSV to', out_path)
    return 0


def _format_cell(v):
    # If value is None: empty cell
    if v is None:
        return ''
    # Primitive types: str/num/bool
    if isinstance(v, (str, int, float, bool)):
        return v
    # Otherwise stringify (safe for JSON objects/arrays)
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


if __name__ == '__main__':
    raise SystemExit(main())


