from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class QueryResult:
    """Normalized result of a query execution.

    Attributes:
        keys: Column names in order.
        rows: List of rows (each row is a sequence of values).
        last_data_update: Human-readable timestamp for when the underlying dataset was last synced.
        query_time_seconds: Query execution duration in seconds.
    """

    keys: list[str]
    rows: list[Sequence[Any]]
    last_data_update: str | None = None
    query_time_seconds: float | None = None


class Datasource(Protocol):
    """Datasource adapter for executing queries."""

    name: str

    def test_connection(self) -> None:
        """Raise on connection issues."""

    def execute(self, query: str) -> QueryResult:
        """Execute query and return normalized result."""
