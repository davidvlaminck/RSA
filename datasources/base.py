from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class QueryResult:
    """Normalized result of a query execution.

    Attributes:
        keys: Column names in order.
        rows: List of rows (each row is a sequence of values, or dict).
        last_data_update: Human-readable timestamp for when the underlying dataset was last synced.
        query_time_seconds: Query execution duration in seconds.
    """

    keys: list[str]
    rows: list[Sequence[Any] | dict[str, Any]]
    last_data_update: str | None = None
    query_time_seconds: float | None = None

    def to_rows_list(self) -> list[list[Any]]:
        """Convert rows to list[list] format, normalizing dicts and tuples.

        This method provides a unified interface for output adapters:
        - If rows are dicts: converts to list based on keys order
        - If rows are tuples/lists: converts to lists

        Use for small to medium resultsets (<10K rows).
        For larger sets, use iter_rows() to avoid memory overhead.
        """
        if not self.rows:
            return []

        first_row = self.rows[0]
        if isinstance(first_row, dict):
            return [[row.get(k) for k in self.keys] for row in self.rows]
        else:
            return [list(row) for row in self.rows]

    def iter_rows(self):
        """Memory-efficient iterator over rows as lists.

        Yields each row as list[Any], converting dicts based on keys order.
        Recommended for large resultsets (>1000 rows) to minimize memory usage.
        """
        for row in self.rows:
            if isinstance(row, dict):
                yield [row.get(k) for k in self.keys]
            else:
                yield list(row)


class Datasource(Protocol):
    """Datasource adapter for executing queries."""

    name: str

    def test_connection(self) -> None:
        """Raise on connection issues."""

    def execute(self, query: str) -> QueryResult:
        """Execute query and return normalized result."""
