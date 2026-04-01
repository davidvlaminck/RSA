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

    def execute(self, query: str) -> QueryResult:
        start = time.time()

        def _fn(cur, conn):
            cur.execute(query)
            rows = cur.fetchall()
            desc = cur.description
            return rows, desc

        rows, desc = self._connector._run_with_connection(_fn, autocommit_for_read=True)

        # Desc can be None for some adapters; derive keys from description or from first row
        keys = [col.name for col in (desc or [])]
        if not keys and rows:
            first_row = rows[0]
            if isinstance(first_row, dict):
                keys = list(first_row.keys())
            elif isinstance(first_row, (list, tuple)) and desc:
                keys = [col.name for col in desc]

        # final fallback: empty list
        if not keys:
            keys = []

        query_time = round(time.time() - start, 2)

        # Set last_data_update to current Brussels time as fallback
        last_data_update = datetime.now(BRUSSELS).strftime("%Y-%m-%d %H:%M:%S")

        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
