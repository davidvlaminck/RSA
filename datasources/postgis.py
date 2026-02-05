from __future__ import annotations

import time
from datetime import datetime, UTC

from lib.connectors.PostGISConnector import SinglePostGISConnector

from .base import QueryResult


class PostGISDatasource:
    name = "PostGIS"

    def __init__(self):
        self._connector = SinglePostGISConnector.get_connector()

    def test_connection(self) -> None:
        # Use pooled connection to validate connectivity instead of reusing main_connection
        def _fn(cur, conn):
            cur.execute("SELECT 1")
            return cur.fetchone()

        self._connector._run_with_connection(_fn, autocommit_for_read=True)

    def execute(self, query: str) -> QueryResult:
        start = time.time()

        def _fn(cur, conn):
            cur.execute(query)
            rows = cur.fetchall()
            desc = cur.description
            return rows, desc

        rows, desc = self._connector._run_with_connection(_fn, autocommit_for_read=True)
        keys = [col.name for col in (desc or [])]
        if not keys and rows and isinstance(rows[0], dict):
            keys = list(rows[0].keys())
        query_time = round(time.time() - start, 2)

        # Set last_data_update to current UTC time as fallback
        last_data_update = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
