from __future__ import annotations
from typing import Any, List
from pathlib import Path

from .excel import ExcelOutput
from outputs.sheets_cell import SheetsCell


class SheetsCompatAdapter:
    """Adapter that exposes a subset of the original SheetsWrapper API but backed by ExcelOutput.

    This provides compatibility for code (DQReport, workers) that expects methods of
    outputs.sheets_wrapper.SheetsWrapper when Google Sheets is not available.
    """

    def __init__(self, excel: ExcelOutput):
        self.excel = excel

    def get_sheets_in_spreadsheet(self, spreadsheet_id: str) -> dict:
        return self.excel.get_sheets_in_spreadsheet(spreadsheet_id)

    def read_data_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str | None = None,
                             return_raw_results: bool = False, value_render_option: str = 'FORMATTED_VALUE'):
        return self.excel.read_data_from_sheet(spreadsheet_id, sheet_name, sheetrange,
                                               return_raw_results=return_raw_results,
                                               value_render_option=value_render_option)

    def read_celldata_from_sheet(self, spreadsheet_id: str | Path, sheet_name: str, sheetrange: str | None = None,
                                 return_raw_results: bool = False):
        # ExcelOutput provides a rich dict when return_raw_results=True
        raw = self.excel.read_celldata_from_sheet(spreadsheet_id, sheet_name, sheetrange, return_raw_results=True)
        if not isinstance(raw, dict):
            # fallback: transform simple values into rowData
            values = raw if isinstance(raw, list) else []
            rowData = []
            for row in values:
                cells = []
                for v in row:
                    cells.append({'userEnteredValue': v, 'formattedValue': str(v) if v is not None else ''})
                rowData.append({'values': cells})
            startRow = 1
            return {'startRow': startRow, 'rowData': rowData}

        # raw is a dict possibly containing 'rowData' and 'range'
        # compute startRow from range if possible
        rng = raw.get('range', None)
        startRow = 1
        if rng and '!' in rng:
            try:
                _, rng_part = rng.split('!', 1)
                left = rng_part.split(':', 1)[0]
                # strip sheetname if present
                digits = ''.join([c for c in left if c.isdigit()])
                startRow = int(digits) if digits else 1
            except Exception:
                startRow = 1

        # Ensure rowData exists: excel already builds it, but fallback to building from values
        rowData = raw.get('rowData')
        if rowData is None:
            values = raw.get('values', [])
            rowData = []
            for row in values:
                cells = []
                for v in row:
                    cells.append({'userEnteredValue': v, 'formattedValue': str(v) if v is not None else ''})
                rowData.append({'values': cells})

        result = {'startRow': startRow, 'rowData': rowData}
        if return_raw_results:
            # include original values/range as well for callers that expect it
            result['values'] = raw.get('values', [])
            result['range'] = raw.get('range', f'{sheet_name}!A1')
        return result

    def write_data_to_sheet(self, spreadsheet_id: str | Path, sheet_name: str, start_cell: str, data: List[List[Any]],
                            value_input_option: str = 'RAW'):
        # ExcelOutput expects rows iterable in the third positional argument
        # We ignore value_input_option since Excel doesn't support it.
        workbook_path = self.excel._resolve_workbook_path(spreadsheet_id)
        # data is a list of rows (majorDimension ROWS)
        return self.excel.write_data_to_sheet(workbook_path, sheet_name, iter(data), start_cell=start_cell, overwrite=True)

    def write_single_cell(self, spreadsheet_id: str | Path, sheet_name: str, cell: str, value: Any) -> None:
        return self.excel.write_single_cell(spreadsheet_id, sheet_name, cell, value)

    def insert_empty_rows(self, spreadsheet_id: str | Path, sheet_name: str, start_cell: str, number_of_rows: int):
        # Simplest approach: read all rows, insert empty rows at the proper index, rewrite sheet.
        workbook_path = self.excel._resolve_workbook_path(spreadsheet_id)
        rows = self.excel.read_data_from_sheet(workbook_path, sheet_name)
        # compute insert index (1-based row number)
        start = SheetsCell(start_cell)
        idx = start.row - 1  # python list index
        # determine number of columns to preserve
        ncols = max((len(r) for r in rows), default=1)
        empty_rows = [[""] * ncols for _ in range(number_of_rows)]
        new_rows = rows[:idx] + empty_rows + rows[idx:]
        # overwrite sheet
        return self.excel.write_data_to_sheet(workbook_path, sheet_name, iter(new_rows), start_cell='A1', overwrite=True)

    def find_first_nonempty_row_from_starting_cell(self, spreadsheet_id: str | Path, sheet_name: str, start_cell: str, max_rows: int = 1000000) -> int:
        return self.excel.find_first_nonempty_row_from_starting_cell(spreadsheet_id, sheet_name, start_cell, max_rows=max_rows)

    def update_row_by_adding_number(self, spreadsheet_id: str | Path, sheet_name: str, cell: str, delta: int) -> None:
        return self.excel.update_row_by_adding_number(spreadsheet_id, sheet_name, cell, delta)

    # keep an alias so callers checking attributes succeed
    def calculate_cell_range_by_data(self, cell_start, data=None):
        # delegate to excel if available; else provide simple estimation
        return self.excel.calculate_cell_range_by_data(cell_start, data)


__all__ = ["SheetsCompatAdapter"]

