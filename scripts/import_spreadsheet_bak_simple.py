#!/usr/bin/env python3
"""Simple importer: read spreadsheet_mapping.csv.bak and write RSA_OneDrive/spreadsheet_mapping.json
This avoids importing the project's mapping module during the import step (which may have import side-effects).
"""
from pathlib import Path
import csv
import json

BAK = Path(__file__).resolve().parents[1] / 'spreadsheet_mapping.csv.bak'
OUT = Path(__file__).resolve().parents[1] / 'RSA_OneDrive' / 'spreadsheet_mapping.json'

if not BAK.exists():
    print('Bake CSV not found:', BAK)
    raise SystemExit(1)

m = {}
with open(BAK, 'r', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for r in reader:
        sid = (r.get('spreadsheet_id') or '').strip()
        fn = (r.get('excel_file') or r.get('spreadsheet_name') or '').strip()
        if not sid or not fn:
            continue
        if not fn.endswith('.xlsx'):
            fn = fn + '.xlsx'
        m[sid] = fn

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as fh:
    json.dump(m, fh, indent=2, ensure_ascii=False)

print('Wrote', len(m), 'mappings to', OUT)

