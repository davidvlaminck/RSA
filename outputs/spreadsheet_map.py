from __future__ import annotations
from pathlib import Path
import csv
import json
import re
from typing import Dict, Optional

# Mapping loader: looks for a CSV at project root named `spreadsheet_mapping.csv` with columns:
# spreadsheet_id, excel_filename
# Also looks for JSON `RSA_OneDrive/spreadsheet_mapping.json` as fallback.
# Additionally, scan `Reports/Report*.py` for inline attributes `spreadsheet_id` and `excel_filename`.

CACHE: Dict[str, str] = {}
LOADED = False

MAPPING_JSON_PATH = Path(__file__).resolve().parents[1] / 'RSA_OneDrive' / 'spreadsheet_mapping.json'
REPORTS_DIR = Path(__file__).resolve().parents[1] / 'Reports'

# regex patterns to extract attributes in Report files
_RE_SPREADSHEET = re.compile(r"spreadsheet_id\s*=\s*['\"](?P<id>[^'\"]+)['\"]")
_RE_EXCELFILE = re.compile(r"excel_filename\s*=\s*['\"](?P<file>[^'\"]+)['\"]")


def _load_mapping() -> None:
    global CACHE, LOADED
    if LOADED:
        return
    CACHE = {}
    proj_root = Path(__file__).resolve().parents[1]
    csv_path = proj_root / 'spreadsheet_mapping.csv'
    bak_csv_path = proj_root / 'spreadsheet_mapping.csv.bak'
    json_path = MAPPING_JSON_PATH

    # 1) load CSV if present (primary)
    for p in (csv_path, bak_csv_path):
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as fh:
                    reader = csv.DictReader(fh)
                    for r in reader:
                        sid = r.get('spreadsheet_id') or r.get('id') or r.get('sheet_id')
                        fn = r.get('excel_filename') or r.get('filename') or r.get('excel_file') or r.get('spreadsheet_name')
                        if sid and fn:
                            # normalize filename
                            fn = fn.strip()
                            if not fn.endswith('.xlsx'):
                                fn = fn + '.xlsx'
                            CACHE[sid.strip()] = fn
            except Exception:
                # best-effort: skip errors reading CSV
                pass

    # 2) load JSON mapping if present (merge/override)
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    for k, v in data.items():
                        CACHE[str(k)] = str(v)
        except Exception:
            pass

    # 3) scan Reports/ for inline attributes
    try:
        if REPORTS_DIR.exists() and REPORTS_DIR.is_dir():
            for p in sorted(REPORTS_DIR.glob('Report*.py')):
                try:
                    text = p.read_text(encoding='utf-8')
                except Exception:
                    continue
                sid_m = _RE_SPREADSHEET.search(text)
                fn_m = _RE_EXCELFILE.search(text)
                if sid_m and fn_m:
                    sid = sid_m.group('id').strip()
                    fn = fn_m.group('file').strip()
                    if sid and fn:
                        if not fn.endswith('.xlsx'):
                            fn = fn + '.xlsx'
                        CACHE[sid] = fn
    except Exception:
        # if any error scanning reports, ignore
        pass

    LOADED = True


def lookup(spreadsheet_id: str) -> Optional[str]:
    """Return excel filename for spreadsheet_id if available."""
    _load_mapping()
    return CACHE.get(spreadsheet_id)


def add_mapping(spreadsheet_id: str, excel_filename: str, persist: bool = True) -> None:
    _load_mapping()
    CACHE[spreadsheet_id] = excel_filename
    if persist:
        try:
            MAPPING_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            # write existing cache to json
            with open(MAPPING_JSON_PATH, 'w', encoding='utf-8') as fh:
                json.dump(CACHE, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass


__all__ = ['lookup', 'add_mapping']

