#!/usr/bin/env python3
"""
Single worker: run a standalone AQL file against ArangoDB and stream results to Excel.

Refactored using the Factory Method pattern so the AQL data source and Excel writer
can be swapped independently. All CLI arguments are generic -- this worker is
parameter-driven, not hard-coded to any specific AQL file.

Usage examples:
  # Resolve ArangoDB connection from a settings JSON file:
  python scripts/exports/export_aql_to_excel.py --aql-file AQL/queries/adres.aql --out ./out/adres.xlsx --settings settings_sample.json

  # Override connection parameters directly on the command line:
  python scripts/exports/export_aql_to_excel.py --aql-file AQL/Verkeersregelaar/Verkeersregelaar_Sturing_VRIBuiteninstallatie.aql --out ./out/sturing.xlsx --host 127.0.0.1 --port 8529 --user myuser --password 'pw' --database awvinfra

  # Pass AQL bind parameters (JSON):
  python scripts/exports/export_aql_to_excel.py --aql-file AQL/Verkeersregelaar/Verkeersregelaar_Sturing_VRIBuiteninstallatie.aql --out ./out/sturing.xlsx --bind '{"asset_short_uri_VR": "onderdeel#Verkeersregelaar", "asset_short_uri_VRIB": "onderdeel#VRIBuiteninstallatie"}'

Notes:
  - The script performs read-only AQL execution; it does not modify the database.
  - Rows are streamed from the cursor and written to Excel row per row (no bulk DataFrame).
  - Requires openpyxl (pip install openpyxl). pandas is no longer required.
"""
from __future__ import annotations

import argparse
import json
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator

# Make the repository root importable so the lib/datasources packages resolve.
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

DEFAULT_SETTINGS_PATH = Path("C://resources//settings_RSA.json")


def load_settings(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_arango_conf(args) -> dict:
    """Resolve ArangoDB connection parameters from CLI overrides or a settings JSON."""
    if args.host and args.port and args.user and args.database:
        return {
            "host": args.host,
            "port": args.port,
            "user": args.user,
            "password": args.password or "",
            "database": args.database,
        }

    settings_path = Path(args.settings) if args.settings else DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    settings = load_settings(settings_path)
    dbs = settings.get("databases", {})
    conf = dbs.get("ArangoDB") or dbs.get("arangodb")
    if not conf:
        raise KeyError(
            "No ArangoDB configuration found in settings file under databases.ArangoDB"
        )
    return conf


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Execute a standalone AQL file and stream results to Excel row by row."
    )
    p.add_argument(
        "--aql-file",
        required=True,
        help="Path to a standalone .aql file holding the AQL query.",
    )
    p.add_argument(
        "--out",
        required=True,
        help="Destination Excel (.xlsx) file path.",
    )
    p.add_argument(
        "--settings",
        help="Path to settings JSON (optional; defaults to RSA_SETTINGS env or settings_sample.json).",
        default=None,
    )
    p.add_argument("--host", help="ArangoDB host (overrides settings).")
    p.add_argument("--port", help="ArangoDB port (overrides settings).")
    p.add_argument("--user", help="ArangoDB username (overrides settings).")
    p.add_argument("--password", help="ArangoDB password (overrides settings).")
    p.add_argument("--database", help="ArangoDB database name (overrides settings).")
    p.add_argument(
        "--bind",
        help="AQL bind parameters as JSON (optional).",
        default="{}",
    )
    return p.parse_args()


def read_aql_file(aql_path: Path) -> str:
    """Read the AQL file, performing existence checks first."""
    if not aql_path.exists():
        raise FileNotFoundError(f"AQL file not found: {aql_path}")
    if not aql_path.is_file():
        raise IsADirectoryError(f"AQL path is not a file: {aql_path}")
    if aql_path.suffix.lower() != ".aql":
        raise ValueError(f"Expected a .aql file, got: {aql_path}")
    return aql_path.read_text(encoding="utf-8")


# ============================================================================
# Factory Method Pattern — Products
# ============================================================================

class AqlDataSource(ABC):
    """Abstract product: executes an AQL query and returns a cursor-like iterable of rows."""

    @abstractmethod
    def execute(self, query: str, bind_vars: dict) -> Any:
        """Execute the AQL query and return a cursor-like iterable of rows."""
        ...


class ExcelWriter(ABC):
    """Abstract product: writes rows to an Excel file."""

    @abstractmethod
    def write(self, out_path: Path, keys: list[str], rows: Iterator[Any]) -> int:
        """Write rows to Excel, returning the number of data rows written."""
        ...


# ============================================================================
# Concrete Products
# ============================================================================

class ArangoAqlDataSource(AqlDataSource):
    """Concrete product: ArangoDB-backed AQL execution via SingleArangoConnector."""

    def __init__(self, conf: dict):
        from datasources.arango import SingleArangoConnector

        SingleArangoConnector.init(
            host=conf.get("host"),
            port=str(conf.get("port")),
            user=conf.get("user"),
            password=conf.get("password"),
            database=conf.get("database"),
        )
        self._db = SingleArangoConnector.get_db()

    def execute(self, query: str, bind_vars: dict) -> Any:
        return self._db.aql.execute(query, bind_vars=bind_vars)


class OpenpyxlExcelWriter(ExcelWriter):
    """Concrete product: writes rows to .xlsx using openpyxl (row-by-row streaming)."""

    def write(self, out_path: Path, keys: list[str], rows: Iterator[Any]) -> int:
        import openpyxl

        out_path.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "AQL_Result"

        # Header row (when keys are known up front).
        if keys:
            ws.append(keys)

        row_count = 0
        # If no keys from the cursor, infer them from the first row preserving order.
        infer_keys = not bool(keys)
        resolved_keys = list(keys)
        for row in rows:
            if infer_keys:
                if isinstance(row, dict):
                    resolved_keys = list(row.keys())
                    ws.append(resolved_keys)
                    ws.append([row.get(k) for k in resolved_keys])
                    infer_keys = False
                else:
                    resolved_keys = [f"col_{i}" for i in range(len(row))]
                    ws.append(resolved_keys)
                    ws.append(list(row))
                    infer_keys = False
            else:
                if isinstance(row, dict):
                    ws.append([row.get(k) for k in resolved_keys])
                else:
                    ws.append(list(row))
            row_count += 1

        wb.save(out_path)
        return row_count


# ============================================================================
# Factory Method Pattern — Creators
# ============================================================================

class AqlDataSourceFactory(ABC):
    """Abstract creator: factory method for AQL data sources."""

    @abstractmethod
    def create(self, conf: dict) -> AqlDataSource:
        """Factory method: create an AQL data source from connection configuration."""
        ...


class ExcelWriterFactory(ABC):
    """Abstract creator: factory method for Excel writers."""

    @abstractmethod
    def create(self) -> ExcelWriter:
        """Factory method: create an Excel writer."""
        ...


class ArangoAqlDataSourceFactory(AqlDataSourceFactory):
    """Concrete creator: produces ArangoDB AQL data sources."""

    def create(self, conf: dict) -> AqlDataSource:
        return ArangoAqlDataSource(conf)


class OpenpyxlExcelWriterFactory(ExcelWriterFactory):
    """Concrete creator: produces openpyxl Excel writers."""

    def create(self) -> ExcelWriter:
        return OpenpyxlExcelWriter()


# ============================================================================
# Exporter (uses factories)
# ============================================================================

class AqlToExcelExporter:
    """Orchestrates AQL execution and Excel writing using injected factories."""

    def __init__(
        self,
        ds_factory: AqlDataSourceFactory,
        writer_factory: ExcelWriterFactory,
    ):
        self._ds_factory = ds_factory
        self._writer_factory = writer_factory

    def export(self, query: str, bind_vars: dict, conf: dict, out_path: Path) -> int:
        # Create the data source via the factory method.
        ds = self._ds_factory.create(conf)

        # Launch the AQL query and obtain a cursor.
        cursor = ds.execute(query, bind_vars)

        # Determine column keys from the cursor metadata.
        keys: list[str] = []
        try:
            if hasattr(cursor, "keys"):
                cursor_keys = cursor.keys()
                if cursor_keys:
                    keys = list(cursor_keys)
        except Exception:
            keys = []

        # Row stream: yield raw cursor rows (dicts or sequences).
        def row_stream() -> Iterator[Any]:
            for row in cursor:
                yield row

        # Write via the factory-created Excel writer.
        writer = self._writer_factory.create()
        return writer.write(out_path, keys, row_stream())


# ============================================================================
# CLI entry point (the single worker)
# ============================================================================

def main() -> int:
    args = parse_args()

    # Parse bind parameters (JSON).
    try:
        bind_vars = json.loads(args.bind) if args.bind else {}
        if not isinstance(bind_vars, dict):
            raise ValueError("--bind must decode to a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Failed to parse --bind JSON: {exc}", file=sys.stderr)
        return 2

    # Resolve connection settings.
    try:
        conf = resolve_arango_conf(args)
    except Exception as exc:
        print(f"Failed to resolve ArangoDB settings: {exc}", file=sys.stderr)
        return 2

    # Read and validate the AQL file.
    aql_path = Path(args.aql_file)
    try:
        query = read_aql_file(aql_path)
    except Exception as exc:
        print(f"Failed to read AQL file: {exc}", file=sys.stderr)
        return 3

    # Build factories and exporter, then run.
    ds_factory = ArangoAqlDataSourceFactory()
    writer_factory = OpenpyxlExcelWriterFactory()
    exporter = AqlToExcelExporter(ds_factory, writer_factory)

    out_path = Path(args.out)
    try:
        row_count = exporter.export(query, bind_vars, conf, out_path)
    except Exception as exc:
        print(f"AQL execution or Excel write failed: {exc}", file=sys.stderr)
        return 4

    print(f"Wrote {row_count} row(s) from '{aql_path}' to '{out_path}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
