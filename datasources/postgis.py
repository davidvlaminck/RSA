from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from lib.connectors.PostGISConnector import SinglePostGISConnector

from .base import QueryResult

BRUSSELS = ZoneInfo('Europe/Brussels')


class PostGISDatasource:
    name = "PostGIS"

    def __init__(self):
        # Expect the connector to be initialized by the runner; raise helpful error if not.
        try:
            self._connector = SinglePostGISConnector.get_connector()
        except RuntimeError:
            raise RuntimeError('SinglePostGISConnector not initialized. Call SinglePostGISConnector.init(...) before using PostGISDatasource')

    def test_connection(self) -> None:
        # Use pooled connection to validate connectivity instead of reusing main_connection
        def _fn(cur, conn):
            cur.execute("SELECT 1")
            return cur.fetchone()

        self._connector._run_with_connection(_fn, autocommit_for_read=True)

    def execute(self, query: str, max_runtime_seconds: int | None = None) -> QueryResult:
        """Execute a PostGIS query with fail-forward semantics.

        ``max_runtime_seconds`` is the wall-clock cap. If the query does not return in
        time we issue ``pg_cancel_backend`` against the active backend from a fresh
        connection so the worker subprocess does not hang on a single bad query.
        """
        start = time.time()
        # Default hard cap: the connector's statement_timeout + 10s grace; the
        # libpq ``statement_timeout`` will kill the query server-side first, and the
        # wrapper here guarantees the worker subprocess returns within that budget
        # even if the cancel fails for some reason.
        if max_runtime_seconds is None:
            max_runtime_seconds = max(60, int(self._connector._default_statement_timeout_ms / 1000) + 10)

        result = self._connector.execute_with_hard_timeout(query, hard_timeout_s=float(max_runtime_seconds))
        if result.get("error") is not None:
            raise result["error"]
        rows = result["rows"]
        desc = result["description"]

        keys = [col.name for col in (desc or [])]
        if not keys and rows:
            first_row = rows[0]
            if isinstance(first_row, dict):
                keys = list(first_row.keys())

        query_time = round(time.time() - start, 2)
        last_data_update = datetime.now(BRUSSELS).strftime("%Y-%m-%d %H:%M:%S")
        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
