from __future__ import annotations

import time
from typing import Any, Sequence

from neo4j.time import DateTime

from Neo4JConnector import SingleNeo4JConnector

from .base import QueryResult


class Neo4JDatasource:
    name = "Neo4J"

    def __init__(self):
        self._connector = SingleNeo4JConnector.get_connector()

    def test_connection(self) -> None:
        with self._connector.driver.session(database=self._connector.db) as session:
            session.run("RETURN 1").consume()

    def execute(self, query: str) -> QueryResult:
        start = time.time()
        with self._connector.driver.session(database=self._connector.db) as session:
            result = session.run(query)
            keys = list(result.keys())
            data = result.data()
        query_time = round(time.time() - start, 2)

        # Last sync timestamp (existing behavior).
        with self._connector.driver.session(database=self._connector.db) as session:
            query_result: DateTime = session.run('MATCH (p:Params) RETURN p.last_update_utc').single()[0]
        last_data_update = query_result.to_native().strftime("%Y-%m-%d %H:%M:%S")

        # Normalize rows in key order.
        rows: list[Sequence[Any]] = [[row.get(k, "") for k in keys] for row in data]

        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
