from __future__ import annotations

from typing import Any, Sequence
import decimal

from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper

from datasources.base import QueryResult
from .base import OutputWriteContext


class GoogleSheetsOutput:
    """Preserves the current behavior of DQReport writing into Google Sheets."""

    name = "GoogleSheets"

    @staticmethod
    def _json_safe_value(value: Any) -> Any:
        # Google Sheets API payload is JSON-encoded. Ensure we don't pass non-serializable types.
        if value is None:
            return None
        if isinstance(value, decimal.Decimal):
            # Keep full precision as string; avoid float rounding surprises.
            return str(value)
        # Common case: return primitives as-is
        if isinstance(value, (str, int, float, bool)):
            return value
        # Fallback: stringify (e.g. dates, datetimes, UUIDs, custom objects)
        return str(value)

    @classmethod
    def _json_safe_table(cls, table: Sequence[Sequence[Any]]) -> list[list[Any]]:
        return [[cls._json_safe_value(v) for v in row] for row in table]

    def write_report(
        self,
        ctx: OutputWriteContext,
        result: QueryResult,
        *,
        startcell: str = "A1",
        add_filter: bool = True,
        persistent_column: str = "",
        persistent_dict: dict[str, str] | None = None,
        convert_columns_to_numbers: list[str] | None = None,
        link_type: str = "awvinfra",
        recalculate_cells: list[tuple[str, str]] | None = None,
    ) -> None:
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        start_sheetcell = SheetsCell(startcell)

        # recreate Resultaat sheet
        sheets_wrapper.delete_sheet(spreadsheet_id=ctx.spreadsheet_id, sheet_name='ResultaatRenameMe')
        sheets_wrapper.create_sheet(spreadsheet_id=ctx.spreadsheet_id, sheet_name='ResultaatRenameMe')
        sheets_wrapper.delete_sheet(spreadsheet_id=ctx.spreadsheet_id, sheet_name='Resultaat')
        sheets_wrapper.rename_sheet(spreadsheet_id=ctx.spreadsheet_id, sheet_name='ResultaatRenameMe',
                                    new_sheet_name='Resultaat')

        # report header lines
        # If last_data_update is empty, try to fill it with current UTC time as fallback
        from datetime import datetime, UTC
        if not result.last_data_update:
            result_last_data_update = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
        else:
            result_last_data_update = result.last_data_update
        report_made_lines = [[f'Rapport gemaakt op {ctx.now_utc} met data uit:'],
                             [f'{ctx.datasource_name}, laatst gesynchroniseerd op {result_last_data_update}']]
        sheets_wrapper.write_data_to_sheet(spreadsheet_id=ctx.spreadsheet_id, sheet_name='Resultaat', start_cell=startcell,
                                           data=self._json_safe_table(report_made_lines))
        start_sheetcell.update_row_by_adding_number(len(report_made_lines))

        # header row
        headerrow = []
        for key in result.keys:
            headerrow.append(key.split('.')[1] if '.' in key else key)
        if persistent_column:
            headerrow.append('opmerkingen (blijvend)')

        table: list[list[Any]] = [headerrow]

        # rows
        persistent_dict = persistent_dict or {}
        for row in result.rows:
            # Convert dict rows to lists using header keys if needed
            if isinstance(row, dict):
                out_row = [row.get(key, '') for key in result.keys]
            else:
                out_row = list(row)
            if persistent_column:
                if out_row and out_row[0] in persistent_dict:
                    out_row.append(persistent_dict[out_row[0]])
                else:
                    out_row.append('')
            table.append(out_row)

        sheets_wrapper.write_data_to_sheet(spreadsheet_id=ctx.spreadsheet_id,
                                           sheet_name='Resultaat',
                                           start_cell=start_sheetcell.cell,
                                           data=self._json_safe_table(table))

        # convert specified columns to numbers
        if convert_columns_to_numbers:
            col_indices = [SheetsCell(col + '1')._column_int - 1 for col in convert_columns_to_numbers]
            for row_index in range(1, len(table)):
                for col_index in col_indices:
                    value = table[row_index][col_index]
                    if value is not None and value != 'None':
                        table[row_index][col_index] = float(value)

        # filter
        if add_filter:
            sheets_wrapper.clear_filter(ctx.spreadsheet_id, 'Resultaat')
            end_sheetcell = start_sheetcell.copy()
            end_sheetcell.update_column_by_adding_number(len(headerrow) - 1)
            end_sheetcell.update_row_by_adding_number(len(table) - 1)
            sheets_wrapper.create_basic_filter(ctx.spreadsheet_id, 'Resultaat', f'{start_sheetcell.cell}:{end_sheetcell.cell}')

        # freeze
        sheets_wrapper.freeze_top_rows(spreadsheet_id=ctx.spreadsheet_id,
                                       sheet_name='Resultaat',
                                       rows=start_sheetcell.row)

        # auto resize
        sheets_wrapper.automatic_resize_columns(spreadsheet_id=ctx.spreadsheet_id,
                                                sheet_name='Resultaat',
                                                number_of_columns=len(headerrow))

        # hyperlink first column
        start_sheetcell.update_row_by_adding_number(1)
        first_column = [r[0] for r in table[1:] if r]
        sheets_wrapper.add_hyperlink_column(spreadsheet_id=ctx.spreadsheet_id,
                                            sheet_name='Resultaat',
                                            start_cell=start_sheetcell.cell,
                                            link_type=link_type,
                                            column_data=first_column)

        # recalc
        if recalculate_cells:
            for sheet_name, cell in recalculate_cells:
                sheets_wrapper.recalculate_formula(sheet_name=sheet_name, spreadsheet_id=ctx.spreadsheet_id, cell=cell)
