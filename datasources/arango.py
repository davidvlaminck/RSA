import logging
from pathlib import Path
from .base import QueryResult

from .ArangoDBConnectionFactory import ArangoDBConnectionFactory
from arango import ArangoClient
from datetime import datetime, timezone

class ArangoDatasource:
    """ArangoDB datasource (AQL)."""

    name = "ArangoDB"

    def __init__(self, db_name: str, username: str, password: str):
        self.factory = ArangoDBConnectionFactory(db_name, username, password)
        self.connection = None
        self.test_connection()

    def _normalize_last_data_update(self, v):
        """Normalize various datetime/string representations to '%Y-%m-%d %H:%M:%S'.
        Accepts: datetime (aware or naive), ISO string with offset, or other string.
        Returns formatted string or None if cannot parse.
        """
        if v is None:
            return None
        # If it's already a datetime
        if isinstance(v, datetime):
            # ensure timezone-aware in UTC for consistent formatting
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            else:
                v = v.astimezone(timezone.utc)
            return v.strftime("%Y-%m-%d %H:%M:%S")
        # If it's a string, try to parse ISO formats
        if isinstance(v, str):
            try:
                # Python 3.11+ supports fromisoformat with offset; use it and fallback
                dt = datetime.fromisoformat(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                # Try a few common formats
                for fmt in ("%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        dt = datetime.strptime(v, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        else:
                            dt = dt.astimezone(timezone.utc)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        continue
        # Can't parse
        return None

    def test_connection(self) -> None:
        if hasattr(self, "factory") and self.factory is not None:
            try:
                self.connection = self.factory.create_connection()
                logging.info(f"✅ Connected to ArangoDB: {self.connection.name}")
            except Exception as e:
                logging.error(f"❌ Failed to connect to ArangoDB: {e}")
                raise
        elif hasattr(self, "connection") and self.connection is not None:
            logging.info("✅ Using existing ArangoDB connection.")
        else:
            raise RuntimeError("No ArangoDB connection or factory available.")

    def execute(self, query: str) -> QueryResult:
        if not hasattr(self, 'connection') or not self.connection:
            raise RuntimeError("No active ArangoDB connection.")
        try:
            import time
            start_time = time.time()
            cursor = self.connection.aql.execute(query)
            result = list(cursor)

            # Try to obtain ordered keys. Some cursors don't expose keys(); infer from first row if possible.
            keys = []
            try:
                if hasattr(cursor, 'keys'):
                    keys = cursor.keys() or []
            except Exception:
                keys = []

            if (not keys) and len(result) > 0 and isinstance(result[0], dict):
                # preserve insertion order of dict
                keys = list(result[0].keys())

            query_time_seconds = round(time.time() - start_time, 2)

            # Try to get last_data_update from the cursor or from params collection
            last_data_update = getattr(cursor, 'last_data_update', None)

            # Normalize if it's present
            normalized = self._normalize_last_data_update(last_data_update)
            if normalized:
                last_data_update = normalized
            else:
                # fallback: try params collection
                try:
                    params_col = self.connection.collection('params')
                    doc = params_col.get('finished_at')
                    if doc and 'value' in doc:
                        normalized = self._normalize_last_data_update(doc['value'])
                        if normalized:
                            last_data_update = normalized
                        else:
                            last_data_update = doc['value']
                except Exception:
                    # ignore failures reading params
                    last_data_update = last_data_update

            return QueryResult(keys=keys, rows=result, query_time_seconds=query_time_seconds, last_data_update=last_data_update)
        except Exception as e:
            logging.error(f"❌ Query execution failed: {e}")
            raise

    @classmethod
    def from_existing_connection(cls, connection):
        obj = cls.__new__(cls)
        # keep compatibility with test_connection checks that look for a 'factory' attribute
        obj.factory = None
        obj.connection = connection
        return obj

class SingleArangoConnector:
    _instance = None
    _db = None

    @classmethod
    def init(cls, host, port, user, password, database):
        if cls._instance is None:
            cls._instance = cls()
            client = ArangoClient(hosts=f'http://{host}:{port}')
            # Connect to ArangoDB server
            try:
                _ = client.db('_system', username=user, password=password)
            except Exception:
                # if system DB connect fails, continue and let later calls surface the error
                pass
            # Connect to the actual database
            cls._db = client.db(database, username=user, password=password)

    @classmethod
    def get_db(cls):
        if cls._db is None:
            raise Exception("SingleArangoConnector not initialized. Call init() first.")
        return cls._db
