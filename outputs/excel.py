from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None

from datasources.base import QueryResult
from .base import OutputWriteContext


class ExcelOutput:
    """Write one .xlsx per report.

    This is a new output implementation for the target use case.
    It is intentionally minimal for now (no formatting bells & whistles yet).
    """

    name = "Excel"

    def __init__(self, output_dir: str = "./out"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        if openpyxl is None:
            raise RuntimeError("openpyxl is required for ExcelOutput")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Resultaat"

        # header lines
        ws.append([f"Rapport gemaakt op {ctx.now_utc} met data uit:"])
        ws.append([f"{ctx.datasource_name}, laatst gesynchroniseerd op {result.last_data_update or ''}"])
        ws.append([])

        headers = [k.split('.')[1] if '.' in k else k for k in result.keys]
        if persistent_column:
            headers.append('opmerkingen (blijvend)')
        ws.append(headers)

        persistent_dict = persistent_dict or {}
        for out_row in result.iter_rows():
            if persistent_column:
                if out_row and out_row[0] in persistent_dict:
                    out_row.append(persistent_dict[out_row[0]])
                else:
                    out_row.append('')
            ws.append(out_row)

        out_path = self.output_dir / f"{ctx.report_title}.xlsx"
        wb.save(out_path)
