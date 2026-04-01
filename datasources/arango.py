import logging
from pathlib import Path
from .base import QueryResult

from .ArangoDBConnectionFactory import ArangoDBConnectionFactory
from arango import ArangoClient
from datetime import datetime
from zoneinfo import ZoneInfo

BRUSSELS = ZoneInfo('Europe/Brussels')

class ArangoDatasource:
    """ArangoDB datasource (AQL)."""

    name = "ArangoDB"

    def __init__(self, db_name: str, username: str, password: str):
        self.factory = ArangoDBConnectionFactory(db_name, username, password)
        self.connection = None
        self.test_connection()

    def _normalize_last_data_update(self, v):
        """Normalize various datetime/string representations to Brussels-local '%Y-%m-%d %H:%M:%S'.
        Accepts: datetime (aware or naive), ISO string with offset, or other string.
        Returns formatted string or None if cannot parse.
        """
        if v is None:
            return None
        # If it's already a datetime
        if isinstance(v, datetime):
            # ensure timezone-aware in Brussels for consistent formatting
            if v.tzinfo is None:
                v = v.replace(tzinfo=BRUSSELS)
            else:
                v = v.astimezone(BRUSSELS)
            return v.strftime("%Y-%m-%d %H:%M:%S")
        # If it's a string, try to parse ISO formats
        if isinstance(v, str):
            try:
                # Python 3.11+ supports fromisoformat with offset; use it and fallback
                dt = datetime.fromisoformat(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=BRUSSELS)
                else:
                    dt = dt.astimezone(BRUSSELS)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                # Try a few common formats
                for fmt in ("%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        dt = datetime.strptime(v, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=BRUSSELS)
                        else:
                            dt = dt.astimezone(BRUSSELS)
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

            # Always provide keys: try cursor metadata first, then infer from rows
            keys: list[str] = []
            try:
                if hasattr(cursor, 'keys'):
                    cursor_keys = cursor.keys()
                    if cursor_keys:
                        keys = list(cursor_keys)
            except Exception:
                keys = []

            # If no keys from cursor, infer by scanning rows preserving first-seen order
            if not keys and len(result) > 0 and isinstance(result[0], dict):
                seen = []
                for row in result:
                    if not isinstance(row, dict):
                        continue
                    for k in row.keys():
                        if k not in seen:
                            seen.append(k)
                keys = seen

            query_time_seconds = round(time.time() - start_time, 2)

            # Try to get last_data_update from the cursor or from params collection
            # Try to get last_data_update from the cursor or from params collection
            last_data_update = getattr(cursor, 'last_data_update', None)

            # Debug: log the raw cursor-provided last_data_update for diagnostics
            try:
                logging.debug('Arango cursor last_data_update (raw): %r', last_data_update)
            except Exception:
                pass

            # Normalize if it's present (cursor may provide it)
            normalized = self._normalize_last_data_update(last_data_update)
            if normalized:
                last_data_update = normalized
                source = 'cursor'
            else:
                # fallback: try params collection with several common keys
                try:
                    params_col = self.connection.collection('params')
                    candidate_keys = ['finished_at', 'last_data_update', 'last_sync', 'updated_at']
                    found = False
                    for key in candidate_keys:
                        try:
                            doc = params_col.get(key)
                        except Exception:
                            doc = None
                        if doc and 'value' in doc and doc.get('value') is not None:
                            try:
                                logging.debug('Arango params.%s raw value: %r', key, doc.get('value'))
                            except Exception:
                                pass
                            normalized = self._normalize_last_data_update(doc['value'])
                            if normalized:
                                last_data_update = normalized
                                source = f'params.{key}.normalized'
                            else:
                                last_data_update = doc['value']
                                source = f'params.{key}.raw'
                            found = True
                            break
                    if not found:
                        last_data_update = None
                except Exception:
                    # ignore failures reading params
                    last_data_update = last_data_update
                    if not locals().get('source'):
                        source = 'unknown'

                # If params didn't yield a timestamp, try inferring from result rows
                if not last_data_update:
                    try:
                        import re as _re
                        candidates = []
                        key_pattern = _re.compile(r'(date|time|updated|modified|finished|ts)', _re.IGNORECASE)
                        for r in result:
                            if not isinstance(r, dict):
                                continue
                            for k, v in r.items():
                                if key_pattern.search(k):
                                    norm = self._normalize_last_data_update(v)
                                    if norm:
                                        candidates.append(norm)
                        if candidates:
                            # parse candidates to datetimes and pick the latest
                            parsed = []
                            for s in candidates:
                                try:
                                    # s is expected as 'YYYY-MM-DD HH:MM:SS'
                                    parsed.append(datetime.fromisoformat(s.replace(' ', 'T')))
                                except Exception:
                                    try:
                                        parsed.append(datetime.strptime(s, '%Y-%m-%d %H:%M:%S'))
                                    except Exception:
                                        pass
                            if parsed:
                                latest = max(parsed)
                                last_data_update = latest.astimezone(BRUSSELS).strftime('%Y-%m-%d %H:%M:%S')
                                source = 'inferred.rows'
                    except Exception:
                        pass

            # Log resolved last_data_update and its source at INFO level for visibility
            try:
                logging.info('Arango last_data_update resolved (source=%s): %r', locals().get('source'), last_data_update)
            except Exception:
                pass

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
