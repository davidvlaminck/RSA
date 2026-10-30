#!/usr/bin/env python3
"""
Thin wrapper: launch export_aql_to_excel worker for Laagspanningsbord_update_toezichtsgroep.aql.

All shared logic lives in export_aql_to_excel.py (the single worker). This file
only supplies the query-specific parameters (AQL file, output path, bind vars).
"""
import sys
from pathlib import Path

# Make the repository root importable so the worker module resolves.
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from export_aql_to_excel import main as worker_main

if __name__ == "__main__":
    project_root = repo_root.resolve().parents[0]
    aql_file = str(project_root / r"AQL\Laagspanningsbord\Laagspanningsbord_update_toezichtsgroep.aql")

    sys.argv = [
        "export_aql_to_excel_Laagspanningsbord_update_toezichtsgroep.py",
        "--aql-file", aql_file,
        "--out", r".\out\DA-2026-69695_laagspanningsbord_update_toezichter.xlsx",
        "--bind", '{"asset_short_uri": "onderdeel#Laagspanningsbord"}',
    ]
    sys.exit(worker_main())
