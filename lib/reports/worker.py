"""Worker script to run a single report in an isolated subprocess.

This worker is invoked by ReportLoopRunner to execute reports in separate processes.
Each process:
- Re-initializes database connections (critical for thread-safety)
- Runs the report with timeout protection
- Returns exit code 0 on success, non-zero on failure

Usage:
    python -m lib.reports.worker --report Report0002 --settings /path/to/settings.json
"""
import argparse
import gc
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from contextvars import ContextVar
import warnings

logger = logging.getLogger(__name__)

# Suppress known third-party DeprecationWarnings (narrow filter)
warnings.filterwarnings('ignore', message=r'path is deprecated. Use files\(\) instead', category=DeprecationWarning)

# Add project root to path so we can import modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Context variable to track current report name for logging
current_report: ContextVar[str] = ContextVar('current_report', default='')


class ReportContextFilter(logging.Filter):
    """Add current report name to all log records."""
    def filter(self, record):
        report_name = current_report.get()
        if report_name:
            record.report_name = report_name
        else:
            record.report_name = 'System'
        return True


def setup_logging():
    """Configure logging for the worker process."""
    
    class _FlushingStreamHandler(logging.StreamHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    
    handler = _FlushingStreamHandler(sys.stdout)
    handler.addFilter(ReportContextFilter())
    formatter = logging.Formatter(
        '[Worker %(process)d] [%(report_name)s] %(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def _write_status(status_file: str | None, report_name: str, success: bool) -> None:
    if not status_file:
        return
    try:
        entry = {"report": report_name, "success": success, "ts": time.time()}
        with open(status_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
            f.flush()
    except Exception:
        pass


def _log_resource_heartbeat() -> None:
    try:
        with open('/proc/meminfo', 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        mem = {line.split(':')[0].strip(): int(line.split(':')[1].strip().split()[0]) for line in lines if ':' in line}
        total = mem.get('MemTotal', 0)
        avail = mem.get('MemAvailable', 0)
        used = total - avail
        mem_pct = (used / total * 100) if total else 0

        with open('/proc/loadavg', 'r', encoding='utf-8') as f:
            load = f.read().split()[0]

        st = os.statvfs('.')
        disk_pct = (1 - st.f_bavail / st.f_blocks) * 100 if st.f_blocks else 0

        logger.info('heartbeat: load=%s, mem=%d/%dMB (%d%%), disk=%d%%', load, used // 1024, total // 1024, int(mem_pct), int(disk_pct))
    except Exception:
        pass


def reinitialize_database_connections(settings, arango_timeout: int = 180):
    """Re-initialize all database singletons in this child process.

    Critical: Forked processes inherit parent connections which are NOT safe to use.
    Each child must create fresh connections.
    """
    databases = settings.get('databases', {}) if isinstance(settings, dict) else {}
    
    neo4j_settings = databases.get('Neo4j')
    if neo4j_settings:
        try:
            SingleNeo4JConnector.reset()
        except Exception:
            pass
        try:
            # Neo4J connector
            from lib.connectors.Neo4JConnector import SingleNeo4JConnector
            SingleNeo4JConnector.init(
                uri=neo4j_settings['uri'],
                user=neo4j_settings['user'],
                password=neo4j_settings['password'],
                database=neo4j_settings['database']
            )
            logger.info("Reinitialized Neo4J connection")
        except Exception as e:
            logger.warning(f"Could not reinitialize Neo4J: {e}")
    else:
        logger.debug("Neo4j settings not configured; skipping reinitialization")

    postgis_settings = databases.get('PostGIS')
    if postgis_settings:
        try:
            SinglePostGISConnector.reset()
        except Exception:
            pass
        try:
            # PostGIS connector
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            SinglePostGISConnector.init(
                host=postgis_settings['host'],
                port=postgis_settings['port'],
                user=postgis_settings['user'],
                password=postgis_settings['password'],
                database=postgis_settings['database']
            )
            logger.info("Reinitialized PostGIS connection")
        except Exception as e:
            logger.warning(f"Could not reinitialize PostGIS: {e}")
    else:
        logger.debug("PostGIS settings not configured; skipping reinitialization")

    arango_settings = databases.get('ArangoDB')
    if arango_settings:
        try:
            from datasources.arango import SingleArangoConnector
            SingleArangoConnector.reset()
        except Exception:
            pass
        try:
            # expose settings so init() can read query_max_runtime / query_memory_limit
            SingleArangoConnector._arango_settings = arango_settings
            SingleArangoConnector.init(
                host=arango_settings['host'],
                port=arango_settings['port'],
                user=arango_settings['user'],
                password=arango_settings['password'],
                database=arango_settings['database'],
                request_timeout=arango_timeout,
            )
            logger.info("Reinitialized ArangoDB connection")
            # Bound server-side query runtime to this attempt's client timeout so a
            # hanging query is aborted on the ArangoDB server itself (not just the client).
            try:
                SingleArangoConnector.set_query_bounds(
                    max_runtime=arango_timeout,
                    memory_limit=arango_settings.get('query_memory_limit'),
                )
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Could not reinitialize ArangoDB: {e}")
    else:
        logger.debug("ArangoDB settings not configured; skipping reinitialization")

    # Ensure Excel writer and Excel-backed Sheets wrapper are initialized for workers.
    # Google Sheets access is no longer used, so this only (re)opens the Excel writer.
    # Called between batches as well, so the Excel writer is released/recreated regularly.
    try:
        drive_cfg = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
        excel_cfg = settings.get('output', {}).get('excel', {}) if isinstance(settings, dict) else {}
        out_dir = drive_cfg.get('local_folder') or excel_cfg.get('output_dir')
        if out_dir is None:
            out_dir = str(Path(settings.get('workdir', Path.cwd())).resolve().parents[0] / 'RSA_OneDrive')
        from outputs.excel_wrapper import SingleExcelWriter
        from outputs.sheets_wrapper import SingleSheetsWrapper
        SingleExcelWriter.init(output_dir=out_dir)
        SingleSheetsWrapper.init(output_dir=out_dir)
        logger.info('Reinitialized Excel writer and Excel-backed Sheets wrapper')
    except Exception as e:
        logger.warning(f'Could not initialize Excel writer in worker: {e}')


def run_single_report(report_name: str, settings: dict, skip_db_init: bool = False) -> int:
    """Run a single report and return exit code.

    Args:
        report_name: Name of report class (e.g., "Report0002")
        settings: Full settings dictionary
        skip_db_init: If True, skip DB reinitialization (already done for pipeline)

    Returns:
        0 on success, 1 on failure
    """
    current_report.set(report_name)

    query_timeout = settings.get('query_timeout_seconds', 60)
    total_timeout = query_timeout * 2

    class _ReportTimeout(Exception):
        pass

    def _cancel_current_query():
        """Cancel the running query on PostgreSQL backend."""
        try:
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            connector = SinglePostGISConnector.get_connector()
            conn = connector.pool.getconn()
            conn.autocommit = True
            try:
                pid = conn.get_backend_pid()
                cur = conn.cursor()
                cur.execute(f"SELECT pg_cancel_backend({pid})")
                cur.fetchall()
                cur.close()
            finally:
                connector.pool.putconn(conn)
        except Exception:
            pass

    def _timeout_handler(signum, frame):
        _cancel_current_query()
        raise _ReportTimeout()

    # Arm the watchdog BEFORE instantiation/initialization so a hang there is also bounded.
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(total_timeout)
    try:
        _log_resource_heartbeat()
        logger.info(f"Starting report")

        if not skip_db_init:
            arango_timeout = settings.get('arango_request_timeout', 180)
            reinitialize_database_connections(settings, arango_timeout=arango_timeout)

        from lib.reports.instantiator import create_report_instance
        report_instance = create_report_instance(report_name)

        if report_instance is None:
            logger.error(f"Failed to instantiate")
            return 1

        report_instance.init_report()
        logger.info(f"Initialized")

        postgis_ms = query_timeout * 1000
        try:
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            connector = SinglePostGISConnector.get_connector()
            connector.set_statement_timeout(postgis_ms)
        except Exception:
            pass
        report_instance.run_report(sender=None)
        signal.alarm(0)
        logger.info(f"✅ Completed report successfully")
        return 0
    except _ReportTimeout:
        signal.alarm(0)
        logger.error(
            f"❌ Timeout after {total_timeout}s for {report_name} "
            f"(query={query_timeout}s) — re-added to retry queue"
        )
        return 1
    except Exception as e:
        signal.alarm(0)
        logger.error(f"❌ Failed: {e} — re-added to retry queue", exc_info=True)
        return 1
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def run_reports(report_names: list[str], settings: dict, status_file: str | None = None,
                batch_size: int = 0, batch_timeout: float = 0, deadline: float = 0) -> int:
    """Run multiple reports sequentially in the same worker process.

    Reinitializes database connections once at the start of the pipeline,
    then reuses them for all subsequent reports in the pipeline.

    Args:
        report_names: List of report names to run.
        settings: Settings dictionary.
        status_file: Optional path to write per-report completion status (JSONL).
        batch_size: Maximum number of reports per batch. 0 means no batching.
        batch_timeout: Maximum seconds per batch. 0 means no batch timeout.
        deadline: Unix timestamp. When reached, report execution stops.

    Returns:
        0 if all reports succeed, 1 if any report fails or times out.
    """
    effective_batch_size = max(1, batch_size) if batch_size else len(report_names)
    batches = [report_names[i:i + effective_batch_size] for i in range(0, len(report_names), effective_batch_size)]

    logger.info(f"Pipeline starting with {len(report_names)} reports in {len(batches)} batch(es) of {effective_batch_size}")
    arango_timeout = settings.get('arango_request_timeout', 180)
    reinitialize_database_connections(settings, arango_timeout=arango_timeout)

    failed = []
    for batch_idx, batch in enumerate(batches):
        batch_start = time.time()
        logger.info(f"Starting batch {batch_idx + 1}/{len(batches)} with {len(batch)} reports")

        for report_name in batch:
            if deadline and time.time() >= deadline:
                logger.warning(
                    f"Deadline reached ({datetime.fromtimestamp(deadline).isoformat()}), "
                    f"stopping after batch {batch_idx + 1}"
                )
                failed.extend(batch[batch.index(report_name):])
                break

            if batch_timeout and (time.time() - batch_start) >= batch_timeout:
                logger.warning(
                    f"Batch timeout ({batch_timeout}s) reached in batch {batch_idx + 1}, "
                    f"stopping before {report_name}"
                )
                failed.extend(batch[batch.index(report_name):])
                break

            exit_code = run_single_report(report_name, settings, skip_db_init=True)
            _write_status(status_file, report_name, exit_code == 0)
            if exit_code != 0:
                failed.append(report_name)

        if deadline and time.time() >= deadline:
            break

        # Reset connection singletons between batches. Each worker is an isolated
        # process, so resetting its own connections is safe and does not affect the
        # other worker process. This releases connection pools / sockets that leaked
        # (e.g. on query timeouts) during the batch just finished, bounding memory
        # growth of the long-lived worker process. The Excel writer (no Google Sheets)
        # is reopened as well to release any held state.
        try:
            reinitialize_database_connections(settings, arango_timeout=arango_timeout)
        except Exception as e:
            logger.warning(f"Could not reset connections between batches: {e}")
        gc.collect()

    _write_status(status_file, '__pipeline_done__', True)

    if failed:
        logger.error("One or more reports failed/timed out in worker: %s", ", ".join(failed))
        return 1
    return 0


def main():
    """Main entry point for the worker."""
    parser = argparse.ArgumentParser(description='Run a single report in isolation')
    parser.add_argument('--report', help='Single report name (e.g., Report0002)')
    parser.add_argument('--reports', nargs='+', help='Multiple report names (e.g., Report0002 Report0004)')
    parser.add_argument('--settings', required=True, help='Path to settings JSON file')
    parser.add_argument('--status-file', help='Path to write per-report completion status (JSONL)')
    parser.add_argument('--batch-size', type=int, default=0, help='Maximum reports per batch (0 = no batching)')
    parser.add_argument('--batch-timeout', type=float, default=0, help='Maximum seconds per batch (0 = no timeout)')
    parser.add_argument('--deadline', type=float, default=0, help='Unix timestamp deadline (0 = no deadline)')

    args = parser.parse_args()

    setup_logging()

    # Load settings
    import json
    with open(args.settings, 'r') as f:
        settings = json.load(f)

    # Run the report(s)
    if args.report:
        report_list = [args.report]
    elif args.reports:
        report_list = args.reports
    else:
        logger.error("You must provide --report or --reports")
        sys.exit(2)

    exit_code = run_reports(
        report_list,
        settings,
        status_file=args.status_file,
        batch_size=args.batch_size,
        batch_timeout=args.batch_timeout,
        deadline=args.deadline,
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
