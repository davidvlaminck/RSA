from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Sequence

from PostGISConnector import SinglePostGISConnector

from .base import Datasource, QueryResult


class PostGISDatasource:
    name = "PostGIS"

    def __init__(self):
        self._connector = SinglePostGISConnector.get_connector()

    def test_connection(self) -> None:
        # A cheap operation that validates the connection.
        with self._connector.main_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    def execute(self, query: str) -> QueryResult:
        start = time.time()
        with self._connector.main_connection.cursor() as cursor:
            cursor.execute(query)
            rows: list[Sequence[Any]] = cursor.fetchall()
            keys = [col.name for col in cursor.description]
        query_time = round(time.time() - start, 2)

        # Keep the existing semantics used by DQReport today.
        params = self._connector.get_params(self._connector.main_connection)
        last_update = params.get("last_update_utc_assets")
        last_data_update = (
            last_update.strftime("%Y-%m-%d %H:%M:%S") if isinstance(last_update, datetime) else None
        )

        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
