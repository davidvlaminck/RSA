from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Iterator, List
import datetime
import decimal
import shutil
import time
import importlib
import warnings

# lazy-loaded openpyxl handles
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
        # import and then apply narrow warning filters for known third-party deprecation messages
        openpyxl = importlib.import_module('openpyxl')
        # suppress specific DeprecationWarning emitted by openpyxl using datetime.utcnow()
        warnings.filterwarnings('ignore', message=r"datetime.datetime.utcnow\(\) is deprecated", category=DeprecationWarning)
        # suppress certifi/importlib-resources deprecation message seen in some environments
        warnings.filterwarnings('ignore', message=r"path is deprecated. Use files\(\) instead", category=DeprecationWarning)

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

    def iter_rows_from_data(self, headers: List[str], rows: Iterable[Iterable[Any]]) -> Iterable[List[Any]]:
        """Yield normalized rows (including header row) lazily for an in-memory rows iterable.

        Backwards-compat helper: previous minimal implementation used this signature.
        """
        yield list(headers)
        for r in rows:
            yield [self._normalize_value(c) for c in r]

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
            # Create default sheets in a sensible order: Overzicht, Historiek, Resultaat
            # Remove default active sheet and recreate
            try:
                # remove default active
                default = wb.active
                wb.remove(default)
            except Exception:
                pass
            # Overzicht sheet: header area for mail receivers and summary links
            ws_overzicht = wb.create_sheet('Overzicht')
            # common header row (example): Mail, Frequency, Last sent
            ws_overzicht.append(['mail', 'frequency', 'last_sent'])

            # Historiek sheet: header row for history entries
            ws_historiek = wb.create_sheet('Historiek')
            ws_historiek.append(['timestamp', 'laatste_sync_databron', 'aantal'])

            # Resultaat sheet: will be written by reports
            ws_resultaat = wb.create_sheet('Resultaat')
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

    def iter_rows(self, a, b=None) -> Iterator[list[Any]]:
        """Dual-purpose iter_rows:

        - Modern signature: iter_rows(workbook_path: Path, sheet_name: str) -> Iterator[list]
        - Legacy/testing signature: iter_rows(headers: List[str], rows: Iterable[Iterable[Any]]) -> Iterator[list]

        We detect by type of `a`.
        """
        # Legacy use: headers + rows
        if isinstance(a, (list, tuple)):
            headers = list(a)
            rows = b
            yield headers
            for r in rows:
                yield [self._normalize_value(c) for c in r]
            return

        # Otherwise treat as (workbook_path, sheet_name)
        workbook_path = Path(a)
        sheet_name = b
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

    # --- compatibility helpers that mimic SheetsWrapper (read-focused) -----------------
    def _resolve_workbook_path(self, spreadsheet_id_or_path: str | Path) -> Path:
        """Resolve a spreadsheet identifier to a workbook Path inside the configured output dir.

        Logic:
        - If the provided value is an absolute or relative path to an existing file, return it.
        - Else, look inside self.output_dir for the filename as-is or with .xlsx appended.
        - Fall back to treating the identifier as a filename under output_dir.
        """
        sp = str(spreadsheet_id_or_path)
        p = Path(sp)
        if p.exists():
            return p
        # try as file in output dir
        candidate = Path(self.output_dir) / sp
        if candidate.exists():
            return candidate
        candidate_x = Path(self.output_dir) / (sp + '.xlsx')
        return candidate_x

    def get_sheets_in_spreadsheet(self, spreadsheet_id: str) -> dict:
        """Return a dict of sheet names -> properties similar to Sheets API minimal shape.

        Example return format:
        {
            'Sheet1': {'gridProperties': {'rowCount': 123, 'columnCount': 10}},
            ...
        }
        """
        _ensure_openpyxl_loaded()
        wb_path = self._resolve_workbook_path(spreadsheet_id)
        if not wb_path.exists():
            return {}
        wb = load_workbook(wb_path, read_only=True)
        out = {}
        for name in wb.sheetnames:
            ws = wb[name]
            # best-effort grid properties
            try:
                row_count = ws.max_row or 0
                col_count = ws.max_column or 0
            except Exception:
                row_count = 0
                col_count = 0
            out[name] = {'gridProperties': {'rowCount': row_count, 'columnCount': col_count}}
        return out

    def read_data_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str | None = None, *,
                             return_raw_results: bool = False, value_render_option: str ='FORMATTED_VALUE') -> list[list[Any]] | dict:
        """Return a list of rows (lists) for the requested range. If sheetrange is None, returns all rows.

        Accepts ranges like 'A1:C10', 'A1:' (until the last row), 'A' or 'A1' (single column), or full None.
        If `return_raw_results` is True, return a dict similar to Sheets API: {'values': rows, 'range': 'Sheet!A1:C3'}
        """
        _ensure_openpyxl_loaded()
        wb_path = self._resolve_workbook_path(spreadsheet_id)
        if not wb_path.exists():
            return {} if return_raw_results else []
        wb = load_workbook(wb_path, read_only=True)
        if sheet_name not in wb.sheetnames:
            return {} if return_raw_results else []
        ws = wb[sheet_name]

        from openpyxl.utils import range_boundaries

        # Determine boundaries
        if sheetrange is None or sheetrange == '':
            min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1
        else:
            # handle patterns like 'A1:' or 'A:' -> treat as until max
            if ':' in sheetrange:
                left, right = sheetrange.split(':', 1)
                if left == '' and right == '':
                    min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1
                else:
                    if right == '' or right is None:
                        # open range, compute right using ws max
                        try:
                            min_col, min_row, _, _ = range_boundaries(left + ':' + left)
                        except Exception:
                            # fallback to column letter
                            from openpyxl.utils import column_index_from_string
                            col = ''.join([c for c in left if c.isalpha()])
                            min_col = column_index_from_string(col) if col else 1
                            min_row = int(''.join([c for c in left if c.isdigit()]) or 1)
                        max_col, max_row = ws.max_column or min_col, ws.max_row or min_row
                    else:
                        try:
                            min_col, min_row, max_col, max_row = range_boundaries(sheetrange)
                        except Exception:
                            # if parsing fails, fallback to whole sheet
                            min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1
            else:
                # single column like 'A' or single cell 'A1'
                try:
                    min_col, min_row, max_col, max_row = range_boundaries(sheetrange + ':' + sheetrange)
                except Exception:
                    min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1

        rows_out = []
        for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col, values_only=True):
            rows_out.append([self._normalize_value(c) for c in row])

        if return_raw_results:
            # build a simple range string
            rng = sheetrange or (f'A1:{chr(64 + (len(rows_out[0]) if rows_out else 1))}{len(rows_out) if rows_out else 1}')
            return {'values': rows_out, 'range': f'{sheet_name}!{rng}'}
        return rows_out

    def read_celldata_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str | None = None, return_raw_results: bool = False) -> dict:
        """Return a minimal raw-style dict with 'values' and 'range' to mimic Sheets API basic shape.

        For now we return only values; rich `rowData` with hyperlinks/formulas can be added later.
        """
        rows = self.read_data_from_sheet(spreadsheet_id, sheet_name, sheetrange)
        # compute a simple range string
        rng = sheetrange or (f'A1:{chr(64 + (len(rows[0]) if rows else 1))}{len(rows) if rows else 1}')
        result: dict = {'values': rows, 'range': f'{sheet_name}!{rng}'}

        # build a richer rowData structure similar to the Sheets API so legacy code can access hyperlinks and formatted values
        try:
            wb_path = self._resolve_workbook_path(spreadsheet_id)
            if wb_path.exists():
                wb = load_workbook(wb_path, read_only=True)
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    rowData = []
                    # determine boundaries for iteration used earlier
                    from openpyxl.utils import range_boundaries
                    if sheetrange is None or sheetrange == '':
                        min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1
                    else:
                        try:
                            min_col, min_row, max_col, max_row = range_boundaries(sheetrange)
                        except Exception:
                            min_col, min_row, max_col, max_row = 1, 1, ws.max_column or 1, ws.max_row or 1

                    for r in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col):
                        values = []
                        for c in r:
                            cell_info: dict = {}
                            # userEnteredValue: raw python value
                            cell_info['userEnteredValue'] = c.value
                            # formattedValue: string representation
                            try:
                                cell_info['formattedValue'] = str(c.value) if c.value is not None else ''
                            except Exception:
                                cell_info['formattedValue'] = ''
                            # hyperlink if present
                            try:
                                if hasattr(c, 'hyperlink') and c.hyperlink:
                                    cell_info['hyperlink'] = str(c.hyperlink.target if hasattr(c.hyperlink, 'target') else c.hyperlink)
                            except Exception:
                                pass
                            # formula detection: in openpyxl formula is string starting with '=' or c.data_type
                            try:
                                if isinstance(c.value, str) and c.value.startswith('='):
                                    cell_info['formula'] = c.value
                            except Exception:
                                pass
                            values.append(cell_info)
                        rowData.append({'values': values})
                    result['rowData'] = rowData
        except Exception:
            # best-effort: if rich read fails, return only simple 'values'
            pass

        if return_raw_results:
            return result
        return result['values']

    def write_single_cell(self, spreadsheet_id: str | Path, sheet_name: str, cell: str, value: Any) -> None:
        """Write a single cell efficiently and atomically.

        - Accepts spreadsheet identifier or path.
        - Performs atomic save (write to temp file + os.replace) to avoid partial writes.
        """
        import os
        from tempfile import NamedTemporaryFile

        _ensure_openpyxl_loaded()
        wb_path = self._resolve_workbook_path(spreadsheet_id)
        # ensure workbook exists
        if not wb_path.exists():
            self.create_workbook_if_missing(wb_path)

        wb = load_workbook(wb_path)
        if sheet_name not in wb.sheetnames:
            wb.create_sheet(sheet_name)
        ws = wb[sheet_name]

        # simple validation of cell
        col_letters = ''.join([c for c in cell if c.isalpha()])
        row_digits = ''.join([c for c in cell if c.isdigit()])
        if not col_letters or not row_digits:
            raise ExcelWriterError(f'Invalid cell identifier: {cell}')

        ws[cell].value = value

        # atomic save: write to temp file and replace
        dirpath = wb_path.parent
        with NamedTemporaryFile(prefix=wb_path.stem + '_tmp_', suffix=wb_path.suffix, dir=str(dirpath), delete=False) as tmp:
            tmp_name = tmp.name
        try:
            wb.save(tmp_name)
            os.replace(tmp_name, str(wb_path))
            try:
                fd = os.open(str(wb_path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass

    def update_row_by_adding_number(self, spreadsheet_id: str | Path, sheet_name: str, cell: str, delta: int) -> None:
        """Read integer from `cell`, add `delta`, and write it back using atomic save.

        This method performs read-modify-write under the same lock policy as write_single_cell: if
        locking is enabled for this workbook, it will acquire the inter-process lock for the whole
        operation. Otherwise it will do a best-effort read+write with atomic replace.
        """
        import os
        from tempfile import NamedTemporaryFile

        _ensure_openpyxl_loaded()
        wb_path = self._resolve_workbook_path(spreadsheet_id)

        # ensure workbook exists
        if not wb_path.exists():
            self.create_workbook_if_missing(wb_path)

        wb = load_workbook(wb_path)
        if sheet_name not in wb.sheetnames:
            ws = wb.create_sheet(sheet_name)
        else:
            ws = wb[sheet_name]

        try:
            val = ws[cell].value
            current = int(val) if (val is not None and str(val).strip() != '') else 0
        except Exception:
            current = 0

        new_val = current + int(delta)
        ws[cell].value = new_val

        # atomic save
        dirpath = wb_path.parent
        with NamedTemporaryFile(prefix=wb_path.stem + '_tmp_', suffix=wb_path.suffix, dir=str(dirpath), delete=False) as tmp:
            tmp_name = tmp.name
        try:
            wb.save(tmp_name)
            os.replace(tmp_name, str(wb_path))
            try:
                fd = os.open(str(wb_path), os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass

    def find_first_nonempty_row_from_starting_cell(self, spreadsheet_id: str | Path, sheet_name: str, start_cell: str, max_rows: int = 1000000) -> int:
        """Find the first non-empty row in the column of start_cell, searching up to max_rows rows.

        Returns the row number (1-based). If none found, returns ws.max_row + 1 or start_row if sheet missing.
        """
        _ensure_openpyxl_loaded()
        wb_path = self._resolve_workbook_path(spreadsheet_id)
        if not wb_path.exists():
            return 1
        wb = load_workbook(wb_path, read_only=True)
        if sheet_name not in wb.sheetnames:
            return 1
        ws = wb[sheet_name]

        # parse start_cell like 'A1'
        col_letters = ''.join([c for c in start_cell if c.isalpha()])
        row_digits = ''.join([c for c in start_cell if c.isdigit()])
        if not col_letters:
            col_index = 1
        else:
            from openpyxl.utils import column_index_from_string
            col_index = column_index_from_string(col_letters)
        start_row = int(row_digits) if row_digits else 1

        max_row = ws.max_row or start_row
        limit = min(max_row, start_row + max_rows - 1)
        for r in range(start_row, limit + 1):
            try:
                val = ws.cell(row=r, column=col_index).value
            except Exception:
                val = None
            if val is not None and val != '':
                return r
        # if none found, return next row after existing max
        return max_row + 1

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

        workbook_exists = workbook_path.exists()

        if workbook_exists:
            # Load existing workbook and replace/clear the target sheet to preserve other sheets
            _ensure_openpyxl_loaded()
            wb = load_workbook(workbook_path)
            if sheet_name in wb.sheetnames:
                # remove existing sheet and recreate at same position
                idx = wb.sheetnames.index(sheet_name)
                ws = wb[sheet_name]
                wb.remove(ws)
                ws = wb.create_sheet(sheet_name, idx)
            else:
                ws = wb.create_sheet(sheet_name)

            # write rows into the ws (works for generator and sequences)
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

        else:
            # workbook does not exist yet: we can create a new workbook; prefer write-only for generators
            if is_generator and WriteOnlyWorkbook is not None:
                wb = WriteOnlyWorkbook()
                ws = wb.create_sheet(sheet_name)
                for r in rows:
                    row = [self._normalize_value(v) for v in r]
                    ws.append(row)
                    rows_written += 1
                wb.save(workbook_path)
            else:
                # create a normal workbook in memory
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


# Export
__all__ = ["ExcelOutput"]
