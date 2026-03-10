"""Scan `Reports/` files for spreadsheet_id and excel_filename attributes and build a mapping.

Writes two files (if mappings found):
- spreadsheet_mapping.csv at project root (columns: spreadsheet_id,excel_filename)
- RSA_OneDrive/spreadsheet_mapping.json with {spreadsheet_id: excel_filename}

This is a best-effort text-based extractor (no importing Reports modules) to avoid side-effects.
"""
from pathlib import Path
import re
import csv
import json

REPORTS_DIR = Path(__file__).resolve().parents[1] / 'Reports'
OUT_CSV = Path(__file__).resolve().parents[1] / 'spreadsheet_mapping.csv'
OUT_JSON = Path(__file__).resolve().parents[1] / 'RSA_OneDrive' / 'spreadsheet_mapping.json'

pattern_spreadsheet = re.compile(r"spreadsheet_id\s*=\s*['\"](?P<id>[^'\"]+)['\"]")
pattern_excelfile = re.compile(r"excel_filename\s*=\s*['\"](?P<file>[^'\"]+)['\"]")

mappings = {}

for p in sorted(REPORTS_DIR.glob('Report*.py')):
    text = p.read_text(encoding='utf-8')
    sid_match = pattern_spreadsheet.search(text)
    file_match = pattern_excelfile.search(text)
    if sid_match and file_match:
        sid = sid_match.group('id').strip()
        fn = file_match.group('file').strip()
        if sid and fn:
            mappings[sid] = fn

if mappings:
    OUT_CSV_parent = OUT_CSV.parent
    OUT_CSV_parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        writer.writerow(['spreadsheet_id', 'excel_filename'])
        for k, v in mappings.items():
            writer.writerow([k, v])

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as fh:
        json.dump(mappings, fh, indent=2)

print('Wrote mappings:', len(mappings))
print('CSV:', OUT_CSV)
print('JSON:', OUT_JSON)

