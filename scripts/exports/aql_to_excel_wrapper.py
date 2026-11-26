#!/usr/bin/env python3
"""
Thin wrapper: launch aql_to_excel_worker.

All shared logic lives in aql_to_excel_worker.py (the single worker). This file
only supplies the query-specific parameters (AQL file, output path, bind vars).
"""
import sys
from pathlib import Path
from datetime import datetime

# Make the repository root importable so the worker module resolves.
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
PROJECT_ROOT = repo_root.resolve().parents[0]
AQL_FILE = PROJECT_ROOT / r"AQL\WVLichtmast\Laagspanningsbord_Voedt_WVLichtmast.aql"
AQL_FILE_NAME = AQL_FILE.stem
from aql_to_excel_worker import main as worker_main

TODAY = datetime.today().strftime('%Y%m%d_%H%M')

# BIND_VARS = '{"agent_naam": "Femke Janssens"}'
#
if __name__ == "__main__":
    sys.argv = [
        "aql_to_excel_wrapper.py",
        "--aql-file", str(AQL_FILE),
        "--out", fr".\out\{TODAY}_{AQL_FILE_NAME}.xlsx",
        # "--bind", BIND_VARS,
    ]
    sys.exit(worker_main())
