import logging
import threading
from types import NoneType

from psycopg2 import Error
from psycopg2.pool import ThreadedConnectionPool
import time


class PostGISCircuitBreaker:
    """Stop trying after consecutive failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = 'closed'

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logging.warning(f"[PostGISConnector] Circuit breaker OPEN after {self.failure_count} failures")

    def record_success(self):
        if self.failure_count > 0:
            logging.info(f"[PostGISConnector] Circuit breaker reset after {self.failure_count} previous failures")
        self.failure_count = 0
        self.state = 'closed'

    def can_execute(self):
        if self.state == 'closed':
            return True
        if self.state == 'open':
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = 'half-open'
                logging.info("[PostGISConnector] Circuit breaker HALF-OPEN, allowing trial request")
                return True
            return False
        return True


class PostGISConnector:
    def __init__(self, host, port, user, password, database: str = 'awvinfra',
                 default_statement_timeout_ms: int = 60000,
                 default_lock_timeout_ms: int = 10000):
        # Statement/lock timeouts are applied via libpq connection options so every
        # connection leaving the pool already has them enforced. This is more robust
        # than running `SET statement_timeout` per-call (which can race with
        # long-running queries on the same connection).
        pool_options = (
            f"-c statement_timeout={int(default_statement_timeout_ms)} "
            f"-c lock_timeout={int(default_lock_timeout_ms)}"
        )
        # keep a modest pool; adjust min/max based on expected concurrent queries
        self.pool = ThreadedConnectionPool(minconn=5, maxconn=30, user=user, password=password, host=host, port=port,
                                           database=database,
                                           keepalives=1,
                                           keepalives_idle=30,
                                           keepalives_interval=10,
                                           keepalives_count=3,
                                           options=pool_options)
        # main_connection kept for legacy usage; prefer using pooled connections for operations
        self.main_connection = self.pool.getconn()
        self.main_connection.autocommit = False
        self.db = database
        self._default_statement_timeout_ms = int(default_statement_timeout_ms)
        self._default_lock_timeout_ms = int(default_lock_timeout_ms)
        self.circuit_breaker = PostGISCircuitBreaker(failure_threshold=5, recovery_timeout=300)
        self.param_type_map = {
            'fresh_start': 'bool',
            'pagesize': 'int',
            'page_agents': 'int',
            'event_uuid_agents': 'text',
            'last_update_utc_agents': 'timestamp',
            'page_assets': 'int',
            'event_uuid_assets': 'text',
            'last_update_utc_assets': 'timestamp',
            'page_assetrelaties': 'int',
            'event_uuid_assetrelaties': 'text',
            'last_update_utc_assetrelaties': 'timestamp',
            'page_betrokkenerelaties': 'int',
            'event_uuid_betrokkenerelaties': 'text',
            'last_update_utc_betrokkenerelaties': 'timestamp',
            'last_update_utc_views': 'timestamp',
            'agents_fill': 'bool',
            'agents_cursor': 'text',
            'toezichtgroepen_fill': 'bool',
            'toezichtgroepen_cursor': 'text',
            'identiteiten_fill': 'bool',
            'identiteiten_cursor': 'text',
            'beheerders_fill': 'bool',
            'beheerders_cursor': 'text',
            'bestekken_fill': 'bool',
            'bestekken_cursor': 'text',
            'assettypes_fill': 'bool',
            'assettypes_cursor': 'text',
            'relatietypes_fill': 'bool',
            'relatietypes_cursor': 'text',
            'assets_fill': 'bool',
            'assets_cursor': 'text',
            'betrokkenerelaties_fill': 'bool',
            'betrokkenerelaties_cursor': 'text',
            'assetrelaties_fill': 'bool',
            'assetrelaties_cursor': 'text',
            'agents_ad_hoc': 'text',
            'assets_ad_hoc': 'text',
            'betrokkenerelaties_ad_hoc': 'text',
            'assetrelaties_ad_hoc': 'text',
            'controlefiches_ad_hoc': 'text',
            'controlefiches_fill': 'bool',
            'controlefiches_cursor': 'text',
            'page_controlefiches': 'int',
            'event_uuid_controlefiches': 'text',
            'last_update_utc_controlefiches': 'timestamp',
        }

    def _validate_connection(self, conn):
        """Check if connection is still alive, close if stale."""
        try:
            if conn.closed:
                return False
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            cur.close()
            return True
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return False

    def _run_with_connection(self, func, *, autocommit_for_read: bool = False, retries: int = 2, retry_backoff: float = 0.5):
        """Helper: get connection from pool, run func(cursor, connection) safely and return value.
        Auto-rollbacks on exceptions and puts connection back to pool.
        Optionally set autocommit_for_read True for read-only queries to avoid long-lived transactions.
        Includes a simple retry loop for transient errors like 'current transaction is aborted'."""
        if not self.circuit_breaker.can_execute():
            raise Error("PostGIS circuit breaker is OPEN - too many consecutive failures, waiting for recovery")

        attempt = 0
        last_exc = None
        while attempt <= retries:
            conn = self.pool.getconn()

            if not self._validate_connection(conn):
                try:
                    self.pool.putconn(conn, close=True)
                except Exception:
                    pass
                conn = self.pool.getconn()

            orig_autocommit = getattr(conn, 'autocommit', False)
            backend_pid = None
            try:
                try:
                    backend_pid = conn.get_backend_pid()
                except Exception:
                    backend_pid = None
                logging.debug(f"[PostGISConnector] _run_with_connection attempt={attempt} backend_pid={backend_pid} autocommit_for_read={autocommit_for_read}")

                # If connection is inside an open transaction and we need to switch
                # autocommit, rollback first because psycopg2 forbids changing
                # autocommit while a transaction is active.
                if autocommit_for_read and not orig_autocommit:
                    try:
                        conn.rollback()
                    except Exception:
                        pass

                # for read-only queries allow autocommit to avoid implicit transaction
                if autocommit_for_read:
                    conn.autocommit = True

                try:
                    cur = conn.cursor()
                    cur.execute(f"SET statement_timeout = {self._default_statement_timeout_ms}")
                    cur.close()
                except Exception:
                    pass

                cur = conn.cursor()
                try:
                    result = func(cur, conn)
                    # commit if we changed autocommit back to False and func didn't raise
                    if not conn.autocommit:
                        try:
                            conn.commit()
                        except Exception as commit_exc:
                            logging.debug(f"[PostGISConnector] commit failed on backend_pid={backend_pid}: {commit_exc}")
                            # if commit fails, ensure rollback next
                            try:
                                conn.rollback()
                            except Exception as rb_exc:
                                logging.debug(f"[PostGISConnector] rollback after failed commit also failed: {rb_exc}")
                    self.circuit_breaker.record_success()
                    return result
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
            except Error as exc:
                last_exc = exc
                # If connection in aborted state, rollback to reset transaction state
                try:
                    conn.rollback()
                    logging.debug(f"[PostGISConnector] rollback executed on backend_pid={backend_pid}")
                except Exception as rb_exc:
                    logging.debug(f"[PostGISConnector] rollback failed on backend_pid={backend_pid}: {rb_exc}")
                # simple heuristic: retry on transaction-aborted or connection-related transient errors
                msg = getattr(exc, 'pgerror', None) or str(exc)
                logging.debug(f"[PostGISConnector] caught Error on backend_pid={backend_pid}: attempt={attempt} exc={exc} pgerror={msg}")
                if 'current transaction is aborted' in msg.lower() or 'terminating connection' in msg.lower() or 'could not receive data from server' in msg.lower():
                    attempt += 1
                    time.sleep(retry_backoff * attempt)
                    # put connection back and try again
                    try:
                        self.pool.putconn(conn, close=False)
                    except Exception as put_exc:
                        logging.debug(f"[PostGISConnector] putconn failed (close=False) on backend_pid={backend_pid}: {put_exc}")
                    logging.debug(f"[PostGISConnector] retrying (attempt {attempt}) after transient error")
                    continue
                # non-retryable: put connection back and reraise
                try:
                    self.pool.putconn(conn, close=False)
                except Exception as put_exc:
                    logging.debug(f"[PostGISConnector] putconn failed (close=False) on backend_pid={backend_pid}: {put_exc}")
                self.circuit_breaker.record_failure()
                raise
            finally:
                # restore autocommit flag and return connection to pool if not already returned
                try:
                    conn.autocommit = orig_autocommit
                except Exception:
                    pass
                try:
                    # putconn may have been called already, but putconn with close=False is idempotent-ish
                    self.pool.putconn(conn)
                except Exception as put_exc:
                    logging.debug(f"[PostGISConnector] putconn final failed on backend_pid={backend_pid}: {put_exc}")
        # exhausted retries
        self.circuit_breaker.record_failure()
        raise last_exc

    def perform_query(self, query: str):
        """Perform a read-only query using a pooled connection and return all rows.
        Uses autocommit for read-only to avoid starting a transaction that may get aborted elsewhere.
        """
        def _fn(cur, conn):
            cur.execute(query)
            return cur.fetchall()

        return self._run_with_connection(_fn, autocommit_for_read=True)

    def execute_with_hard_timeout(self, query: str, hard_timeout_s: float = 60.0):
        """Run a query with a hard wall-clock timeout.

        psycopg2's ``cursor.execute`` is a blocking syscall and is *not* interruptible
        by Python signals; in practice that means a hung backend can keep a worker
        subprocess alive for hours. This wrapper runs the query in a daemon thread and,
        if it does not return in time, asks PostgreSQL to cancel it via a *separate*
        pooled connection (``pg_cancel_backend``).

        Returns a dict with ``rows``, ``description`` and ``error`` keys. Exactly
        one of ``rows``/``error`` is non-None on success/clean timeout. The
        ``description`` is the cursor description object captured before ``fetchall``
        returns, used by callers to derive column names.
        """
        result: dict = {"rows": None, "description": None, "error": None}

        def _runner():
            def _fn(cur, conn):
                cur.execute(query)
                desc = cur.description
                rows = cur.fetchall()
                return rows, desc
            try:
                rows, desc = self._run_with_connection(_fn, autocommit_for_read=True)
                result["rows"] = rows
                result["description"] = desc
            except Exception as exc:  # noqa: BLE001
                result["error"] = exc

        thread = threading.Thread(target=_runner, name="PostGISHardTimeoutQuery", daemon=True)
        thread.start()
        thread.join(timeout=hard_timeout_s)
        if thread.is_alive():
            # The query is still running in the daemon thread. The connection it holds
            # is locked inside psycopg2.execute, so we cannot reuse it to issue
            # pg_cancel_backend on the same backend PID; instead we pick a *fresh*
            # connection from the pool and cancel by guessing the active backend
            # against pg_stat_activity for this database.
            try:
                cancel_conn = self.pool.getconn()
                try:
                    cancel_conn.autocommit = True
                    cur = cancel_conn.cursor()
                    cur.execute(
                        "SELECT pg_cancel_backend(pid) FROM pg_stat_activity "
                        "WHERE state = 'active' AND datname = current_database() "
                        "AND pid <> pg_backend_pid()"
                    )
                    cur.fetchall()
                    cur.close()
                finally:
                    self.pool.putconn(cancel_conn)
            except Exception:  # noqa: BLE001
                logging.debug("[PostGISConnector] failed to issue pg_cancel_backend on hard timeout")
            # Give Postgres a brief grace period to apply the cancel.
            thread.join(timeout=5.0)
            if thread.is_alive():
                logging.error(
                    "[PostGISConnector] query did not respond to pg_cancel_backend within 5s; "
                    "the worker subprocess will keep running until the outer deadline kills it"
                )
            result["error"] = TimeoutError(
                f"PostGIS query exceeded hard timeout of {hard_timeout_s}s"
            )
        return result

    def set_statement_timeout(self, ms: int) -> None:
        """Persistently update the statement_timeout used for *new* connections.

        The default timeout is enforced through libpq options at pool construction,
        so changing the value here also affects connections issued afterwards. We do
        not run a SET here because that would require grabbing another pooled
        connection (which may itself be busy with a stuck query) and is therefore
        prone to the very hangs this method is meant to prevent.
        """
        self._default_statement_timeout_ms = int(ms)

    def set_default_statement_timeout(self, ms: int):
        """Set default statement_timeout for new connections."""
        self._default_statement_timeout_ms = int(ms)

    def get_params(self, connection):
        cursor = connection.cursor()
        try:
            cursor.execute('SELECT key_name, value_int, value_text, value_bool, value_timestamp '
                           'FROM public.params')
            raw_param_records = cursor.fetchall()
            params = {}
            for raw_param_record in raw_param_records:
                self.add_params_entry(params_dict=params, raw_param_record=raw_param_record)

            cursor.close()
            return params
        except Error as error:
            if '"public.params" does not exist' in getattr(error, 'pgerror', str(error)):
                cursor.close()
                try:
                    connection.rollback()
                except Exception:
                    pass
                return None
            else:
                logging.error("Error while connecting to PostgreSQL: %s", error)
                cursor.close()
                try:
                    connection.rollback()
                except Exception:
                    pass
                raise error

    def update_params(self, params: dict, connection):
        query = ''
        for key_name, value in params.items():
            param_type = self.param_type_map[key_name]
            if value is None:
                query += f"UPDATE public.params SET value_{param_type} = NULL WHERE key_name = '{key_name}';"
            elif param_type in ['int', 'bool']:
                query += f"UPDATE public.params SET value_{param_type} = {value} WHERE key_name = '{key_name}';"
            else:
                query += f"UPDATE public.params SET value_{param_type} = '{value}' WHERE key_name = '{key_name}';"

        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    @staticmethod
    def delete_params(params: dict, connection):
        query = f"""DELETE FROM public.params WHERE key_name in ('{"','".join(params.keys())}');"""
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def create_params(self, params: dict, connection):
        query = ''
        for key_name, value in params.items():
            param_type = self.param_type_map[key_name]
            if value is None:
                query += f"""INSERT INTO public.params(key_name, value_{param_type})
                             VALUES ('{key_name}', NULL);"""
            elif param_type in ['int', 'bool']:
                query += f"""INSERT INTO public.params(key_name, value_{param_type})
                             VALUES ('{key_name}', {value});"""
            else:
                query += f"""INSERT INTO public.params(key_name, value_{param_type})
                                             VALUES ('{key_name}', '{value}');"""

        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def add_params_entry(self, params_dict, raw_param_record):
        param_type = self.param_type_map.get(raw_param_record[0], None)
        if param_type == 'int':
            params_dict[raw_param_record[0]] = raw_param_record[1]
        elif param_type == 'text' or param_type is None:
            params_dict[raw_param_record[0]] = raw_param_record[2]
        elif param_type == 'bool':
            params_dict[raw_param_record[0]] = raw_param_record[3]
        elif param_type == 'timestamp':
            params_dict[raw_param_record[0]] = raw_param_record[4]
        else:
            raise NotImplementedError

    def get_connection(self, *, autocommit: bool = False):
        connection = self.pool.getconn()
        connection.autocommit = autocommit
        return connection

    def kill_connection(self, connection):
        try:
            # ensure no open transaction remains
            try:
                connection.rollback()
            except Exception:
                pass
            self.pool.putconn(connection)
        except Exception:
            pass


class SinglePostGISConnector:
    postgis_connector: PostGISConnector | NoneType = None

    @classmethod
    def init(cls, host: str = '', port: str = '', user: str = '', password: str = '',
             database: str = 'awvinfra',
             default_statement_timeout_ms: int = 60000,
             default_lock_timeout_ms: int = 10000):
        cls.postgis_connector = PostGISConnector(
            host, port, user, password, database,
            default_statement_timeout_ms=default_statement_timeout_ms,
            default_lock_timeout_ms=default_lock_timeout_ms,
        )

    @classmethod
    def reset(cls):
        if cls.postgis_connector is not None:
            try:
                cls.postgis_connector.pool.closeall()
            except Exception:
                pass
            try:
                if getattr(cls.postgis_connector, 'main_connection', None) is not None:
                    try:
                        cls.postgis_connector.main_connection.close()
                    except Exception:
                        pass
            except Exception:
                pass
        cls.postgis_connector = None

    @classmethod
    def get_connector(cls) -> PostGISConnector:
        if cls.postgis_connector is None:
            raise RuntimeError('Run the init method of this class first')
        return cls.postgis_connector
