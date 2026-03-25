#!/usr/bin/env python3
"""Import mappings from spreadsheet_mapping.csv.bak (or any CSV) into RSA_OneDrive/spreadsheet_mapping.json

Usage: python scripts/import_spreadsheet_bak.py [path-to-csv]
"""
from pathlib import Path
import csv
import sys

from outputs.spreadsheet_map import add_mapping

DEFAULT = Path(__file__).resolve().parents[1] / 'spreadsheet_mapping.csv.bak'

p = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
if not p.exists():
    print('CSV not found:', p)
    sys.exit(1)

count = 0
with open(p, 'r', encoding='utf-8') as fh:
    # attempt to detect delimiter and header
    reader = csv.DictReader(fh)
    for r in reader:
        sid = r.get('spreadsheet_id') or r.get('spreadsheetId') or r.get('id')
        fn = r.get('excel_file') or r.get('excel_file') or r.get('spreadsheet_name') or r.get('spreadsheet_name')
        if sid and fn:
            # ensure filename has .xlsx
            fns = fn
            if not fns.endswith('.xlsx'):
                fns = fns + '.xlsx'
            add_mapping(sid.strip(), fns.strip(), persist=False)
            count += 1

# Now call add_mapping once with persist=True to write the JSON file
# (we need to import outputs.spreadsheet_map and write current CACHE)
from outputs.spreadsheet_map import CACHE, MAPPING_JSON_PATH
MAPPING_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
import json
with open(MAPPING_JSON_PATH, 'w', encoding='utf-8') as fh:
    json.dump(CACHE, fh, indent=2, ensure_ascii=False)

print('Imported', count, 'mappings to', MAPPING_JSON_PATH)

