from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from datasources.base import QueryResult


@dataclass(frozen=True)
class OutputWriteContext:
    spreadsheet_id: str
    report_title: str
    datasource_name: str
    now_utc: str


class ReportOutput(Protocol):
    name: str

    def write_report(self, ctx: OutputWriteContext, result: QueryResult, *,
                     startcell: str = "A1",
                     add_filter: bool = True,
                     persistent_column: str = "",
                     persistent_dict: dict[str, str] | None = None,
                     convert_columns_to_numbers: list[str] | None = None,
                     link_type: str = "awvinfra",
                     recalculate_cells: list[tuple[str, str]] | None = None) -> None:
        """Write the report output. Implementations decide what spreadsheet_id means."""
