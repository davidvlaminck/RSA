import logging
from pathlib import Path
from .base import QueryResult

from .ArangoDBConnectionFactory import ArangoDBConnectionFactory
from arango import ArangoClient

class ArangoDatasource:
    """ArangoDB datasource (AQL)."""

    name = "ArangoDB"

    def __init__(self, db_name: str, username: str, password: str):
        self.factory = ArangoDBConnectionFactory(db_name, username, password)
        self.connection = None
        self.test_connection()

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
            if not last_data_update:
                try:
                    params_col = self.connection.collection('params')
                    doc = params_col.get('finished_at')
                    if doc and 'value' in doc:
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
