from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Iterator
import datetime
import decimal
import shutil
import time
import importlib

openpyxl = None
Workbook = None
WriteOnlyWorkbook = None
get_column_letter = None
load_workbook = None

def _ensure_openpyxl_loaded():
    global openpyxl, Workbook, WriteOnlyWorkbook, get_column_letter, load_workbook
    if openpyxl is not None:
        return
    try:
        openpyxl = importlib.import_module('openpyxl')
        mod = openpyxl
        Workbook = getattr(mod, 'Workbook')
        load_workbook = getattr(mod, 'load_workbook')
        # WriteOnlyWorkbook location can vary; prefer writer.write_only
        # WriteOnlyWorkbook is in openpyxl.writer.write_only
        try:
            wmod = importlib.import_module('openpyxl.writer.write_only')
            WriteOnlyWorkbook = getattr(wmod, 'WriteOnlyWorkbook')
        except Exception:
            # fallback: try alternative path
            try:
                from openpyxl.writer.write_only import WriteOnlyWorkbook as _W
                WriteOnlyWorkbook = _W
            except Exception:
                WriteOnlyWorkbook = None
        try:
            utils_mod = importlib.import_module('openpyxl.utils')
            get_column_letter = getattr(utils_mod, 'get_column_letter')
        except Exception:
            try:
                from openpyxl.utils import get_column_letter as _g
                get_column_letter = _g
            except Exception:
                get_column_letter = None
    except Exception:
        openpyxl = None
        Workbook = None
        WriteOnlyWorkbook = None
        get_column_letter = None
        load_workbook = None
        raise

from datasources.base import QueryResult
from .base import OutputWriteContext


class ExcelWriterError(Exception):
    pass


class ExcelOutput:
    """Write one .xlsx per report.

    The class offers a small helper API for creating workbooks/sheets and streaming rows.
    It is intentionally minimal for now (no formatting bells & whistles yet).
    """

    name = "Excel"

    def __init__(self, output_dir: str = "RSA_OneDrive"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # --- helpers -----------------------------------------------------------------
    def _normalize_value(self, val: Any) -> Any:
        if val is None:
            return ''
        if isinstance(val, decimal.Decimal):
            try:
                return float(val)
            except Exception:
                return str(val)
        if isinstance(val, (datetime.datetime, datetime.date)):
            # use ISO-format for clarity (no timezone conversion here)
            return val.isoformat()
        return val

    def backup_file(self, workbook_path: Path) -> Path:
        if not workbook_path.exists():
            return workbook_path
        ts = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        backup = workbook_path.with_name(f"{workbook_path.stem}_backup_{ts}{workbook_path.suffix}")
        shutil.copy2(workbook_path, backup)
        return backup

    def create_workbook_if_missing(self, workbook_path: Path) -> Path:
        workbook_path = Path(workbook_path)
        _ensure_openpyxl_loaded()
        if not workbook_path.exists():
            wb = Workbook()
            wb.active.title = "Resultaat"
            wb.save(workbook_path)
        return workbook_path

    def create_sheet(self, workbook_path: Path, sheet_name: str, clear_if_exists: bool = True) -> None:
        workbook_path = Path(workbook_path)
        _ensure_openpyxl_loaded()
        self.create_workbook_if_missing(workbook_path)
        wb = load_workbook(workbook_path)
        if sheet_name in wb.sheetnames:
            if clear_if_exists:
                ws = wb[sheet_name]
                # remove all rows: easiest by recreating sheet
                idx = wb.sheetnames.index(sheet_name)
                wb.remove(ws)
                wb.create_sheet(sheet_name, idx)
        else:
            wb.create_sheet(sheet_name)
        wb.save(workbook_path)

    def iter_rows(self, workbook_path: Path, sheet_name: str) -> Iterator[list[Any]]:
        workbook_path = Path(workbook_path)
        if not workbook_path.exists():
            return
            yield  # pragma: no cover
        _ensure_openpyxl_loaded()
        wb = load_workbook(workbook_path, read_only=True)
        if sheet_name not in wb.sheetnames:
            return
            yield  # pragma: no cover
        ws = wb[sheet_name]
        for row in ws.iter_rows(values_only=True):
            yield [self._normalize_value(c) for c in row]

    def clear_sheet_range(self, workbook_path: Path, sheet_name: str, cell_range: str) -> None:
        workbook_path = Path(workbook_path)
        if not workbook_path.exists():
            return
        _ensure_openpyxl_loaded()
        wb = load_workbook(workbook_path)
        if sheet_name not in wb.sheetnames:
            return
        ws = wb[sheet_name]
        # naive clear: iterate cells in range
        try:
            cells = ws[cell_range]
            # cells can be tuple of tuples
            for r in cells:
                for c in r:
                    c.value = None
            wb.save(workbook_path)
        except Exception:
            # fallback: recreate sheet
            ws = wb[sheet_name]
            idx = wb.sheetnames.index(sheet_name)
            wb.remove(ws)
            wb.create_sheet(sheet_name, idx)
            wb.save(workbook_path)

    # --- core write function ----------------------------------------------------
    def write_data_to_sheet(self, workbook_path: Path, sheet_name: str, rows: Iterable[Iterable[Any]],
                            start_cell: str = 'A1', overwrite: bool = True, use_write_only_for_nrows: int = 10000) -> dict:
        """Write rows to a sheet. Rows can be generator. Returns metadata dict."""
        try:
            _ensure_openpyxl_loaded()
        except Exception:
            raise ExcelWriterError('openpyxl not available')

        workbook_path = Path(workbook_path)
        # ensure parent dir
        workbook_path.parent.mkdir(parents=True, exist_ok=True)

        # If overwriting, backup existing file
        if overwrite and workbook_path.exists():
            try:
                self.backup_file(workbook_path)
            except Exception:
                pass

        # Try to write using WriteOnly if rows is a generator and large
        # We don't know rowcount ahead of time; detect generators by lack of __len__
        is_generator = not hasattr(rows, '__len__')

        start_time = time.time()
        rows_written = 0

        if is_generator:
            # use write-only workbook to stream
            if WriteOnlyWorkbook is None:
                # fallback: write into a normal workbook (may use more memory)
                if Workbook is None:
                    raise ExcelWriterError('Neither WriteOnlyWorkbook nor Workbook available')
                logging_warning = False
                try:
                    import logging
                    logging.getLogger(__name__).warning('WriteOnlyWorkbook not available; falling back to Workbook (in-memory)')
                except Exception:
                    pass
                wb = Workbook()
                ws = wb.active
                ws.title = sheet_name
                for r in rows:
                    row = [self._normalize_value(v) for v in r]
                    ws.append(row)
                    rows_written += 1
                wb.save(workbook_path)
                # ensure data is flushed to disk so other processes/threads see the file immediately
                try:
                    import os
                    fd = os.open(str(workbook_path), os.O_RDONLY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                except Exception:
                    # best-effort: ignore fsync errors
                    pass
            else:
                wb = WriteOnlyWorkbook()
                ws = wb.create_sheet(sheet_name)
                # write header area is expected to be included in rows by caller
                for r in rows:
                    row = [self._normalize_value(v) for v in r]
                    ws.append(row)
                    rows_written += 1
                wb.save(workbook_path)
        else:
            # rows is a sequence
            if Workbook is None:
                raise ExcelWriterError('Workbook not available')
            wb = Workbook()
            ws = wb.active
            ws.title = sheet_name
            for r in rows:
                row = [self._normalize_value(v) for v in r]
                ws.append(row)
                rows_written += 1
            wb.save(workbook_path)
            try:
                import os
                fd = os.open(str(workbook_path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except Exception:
                pass

        elapsed = time.time() - start_time
        return {'rows_written': rows_written, 'elapsed_seconds': elapsed, 'file': str(workbook_path)}

    # --- compatibility entrypoint used by DQReport --------------------------------
    def write_report(self, ctx: OutputWriteContext, result: QueryResult, *,
                     startcell: str = "A1",
                     add_filter: bool = True,
                     persistent_column: str = "",
                     persistent_dict: dict[str, str] | None = None,
                     convert_columns_to_numbers: list[str] | None = None,
                     link_type: str = "awvinfra",
                     recalculate_cells: list[tuple[str, str]] | None = None) -> None:
        try:
            _ensure_openpyxl_loaded()
        except Exception:
            raise ExcelWriterError('openpyxl required')

        # determine output filename: prefer ctx.excel_filename if provided
        if hasattr(ctx, 'excel_filename') and ctx.excel_filename:
            out_path = self.output_dir / ctx.excel_filename
        else:
            # fallback to title-based filename
            safe_title = ctx.report_title.replace('/', '_')
            out_path = self.output_dir / f"{safe_title}.xlsx"

        # prepare rows generator: include header and metadata lines similar to Google implementation
        def row_generator():
            yield [f"Rapport gemaakt op {ctx.now_utc} met data uit:"]
            yield [f"{ctx.datasource_name}, laatst gesynchroniseerd op {result.last_data_update or ''}"]
            yield []

            headers = [k.split('.')[-1] for k in result.keys]
            if persistent_column:
                headers = headers + ['opmerkingen (blijvend)']
            yield headers

            persistent_dict_local = persistent_dict or {}
            for out_row in result.iter_rows():
                row = list(out_row)
                if persistent_column:
                    if row and row[0] in persistent_dict_local:
                        row.append(persistent_dict_local[row[0]])
                    else:
                        row.append('')
                yield row

        # write streaming
        meta = self.write_data_to_sheet(out_path, 'Resultaat', row_generator(), start_cell=startcell, overwrite=True)

        # update summary/historiek is still performed by DQReport via Google Sheets wrapper
        return meta

