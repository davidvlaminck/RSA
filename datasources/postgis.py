from __future__ import annotations

import time
import os
import json
from pathlib import Path
from datetime import datetime, UTC

from lib.connectors.PostGISConnector import SinglePostGISConnector

from .base import QueryResult


class PostGISDatasource:
    name = "PostGIS"

    def __init__(self):
        # Try to get existing connector; if not initialized, attempt auto-init from settings file.
        try:
            self._connector = SinglePostGISConnector.get_connector()
        except RuntimeError:
            # Try to auto-initialize using RSA_SETTINGS env var or default settings path
            settings_path = os.environ.get('RSA_SETTINGS') or str(Path.home() / 'Documenten' / 'AWV' / 'resources' / 'settings_RSA.json')
            try:
                if Path(settings_path).exists():
                    with open(settings_path, 'r', encoding='utf-8') as fh:
                        settings = json.load(fh)
                    postgis_conf = settings.get('databases', {}).get('PostGIS') or settings.get('databases', {}).get('postgis')
                    if postgis_conf:
                        SinglePostGISConnector.init(host=postgis_conf.get('host'), port=str(postgis_conf.get('port')),
                                                    user=postgis_conf.get('user'), password=postgis_conf.get('password'),
                                                    database=postgis_conf.get('database'))
                        self._connector = SinglePostGISConnector.get_connector()
                    else:
                        raise
                else:
                    raise
            except Exception:
                # re-raise original helpful message
                raise RuntimeError('Run the init method of SinglePostGISConnector first (or set RSA_SETTINGS to a valid settings file)')

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

        # Set last_data_update to current UTC time as fallback
        last_data_update = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        return QueryResult(keys=keys, rows=rows, last_data_update=last_data_update, query_time_seconds=query_time)
