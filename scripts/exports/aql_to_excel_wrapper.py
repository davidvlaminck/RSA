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

from aql_to_excel_worker import main as worker_main

TODAY = datetime.today().strftime('%Y%m%d_%H%M')

if __name__ == "__main__":
    project_root = repo_root.resolve().parents[0]
    aql_file = str(project_root / r"AQL\queries\Update_toezichter.aql")

    sys.argv = [
        "aql_to_excel_wrapper.py",
        "--aql-file", aql_file,
        "--out", fr".\out\{TODAY}_Update_toezichter.xlsx",
        "--bind", '{"agent_naam": "Femke Janssens"}',
    ]
    sys.exit(worker_main())
