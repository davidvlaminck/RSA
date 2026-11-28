from __future__ import annotations

import json
import logging
import os
import sys
import atexit
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from lib.reports.ReportLoopRunner import ReportLoopRunner
from scripts.ops.drive_sync_gate import DailySharePointSyncGate, upload_after_run
from scripts.ops.sharepoint_sync import prune_daily_run_logs

logger = logging.getLogger(__name__)


DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent / 'config' / 'settings_RSA.json'
BRUSSELS = ZoneInfo('Europe/Brussels')


class _DailyLogTee:
    def __init__(self, original, sink):
        self._original = original
        self._sink = sink
        self._lock = threading.Lock()

    def write(self, data):
        with self._lock:
            self._original.write(data)
            self._sink.write(data)
            self._sink.flush()
        return len(data)

    def flush(self):
        with self._lock:
            self._original.flush()
            self._sink.flush()


def _enable_daily_console_capture(local_folder: str) -> None:
    now = datetime.now(BRUSSELS)
    logs_dir = Path(local_folder) / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    prune_daily_run_logs(local_folder, keep=14)
    log_path = logs_dir / f'run_{now:%Y%m%d}.log'
    sink = open(log_path, 'a', encoding='utf-8', buffering=1)
    sys.stdout = _DailyLogTee(sys.stdout, sink)
    sys.stderr = _DailyLogTee(sys.stderr, sink)
    atexit.register(sink.close)

    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _resolve_path(path_value: str, base_dir: Path) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return str(path)


def _load_runtime_config(settings_path: str) -> dict:
    with open(settings_path, 'r', encoding='utf-8') as fh:
        settings = json.load(fh)

    settings_dir = Path(settings_path).resolve().parent
    rsa_root = Path(__file__).resolve().parent  # RSA repo root; config/ is a sibling, not a parent
    drive_cfg = settings.get('sharepoint_sync', {}) if isinstance(settings, dict) else {}
    output_cfg = settings.get('output', {}) if isinstance(settings, dict) else {}
    excel_cfg = output_cfg.get('excel', {}) if isinstance(output_cfg, dict) else {}
    pipeline_state_cfg = settings.get('pipeline_state', {}) if isinstance(settings, dict) else {}

    local_folder_raw = drive_cfg.get('local_folder') or excel_cfg.get('output_dir') or 'RSA_OneDrive'
    pipeline_state_raw = pipeline_state_cfg.get('db_path', '')

    return {
        'settings_path': settings_path,
        'local_folder': _resolve_path(local_folder_raw, rsa_root),
        'sharepoint_sync_enabled': bool(drive_cfg.get('enabled', True)),
        'sharepoint_sync_after': drive_cfg.get('sync_after', '01:00:00'),
        'sharepoint_folder': drive_cfg.get('sharepoint_folder', 'RSA'),
        'sharepoint_poll_after': drive_cfg.get('poll_after', '00:30:00'),
        'sharepoint_poll_deadline': drive_cfg.get('poll_deadline', '06:00:00'),
        'pipeline_state': {
            'enabled': bool(pipeline_state_cfg.get('enabled', True)),
            'db_path': _resolve_path(pipeline_state_raw, settings_dir) if pipeline_state_raw else '',
            'wait_timeout_seconds': pipeline_state_cfg.get('wait_timeout_seconds', 7200),
            'passive_wait_until': pipeline_state_cfg.get('passive_wait_until', '00:30:00'),
            'postgis_wait_timeout_seconds': pipeline_state_cfg.get('postgis_wait_timeout_seconds', 10800),
        },
    }


def _default_settings_path() -> str:
    """Resolve settings path for local runs (PyCharm Play friendly)."""
    env_path = os.getenv('RSA_SETTINGS')
    if env_path:
        return env_path

    return str(DEFAULT_SETTINGS_PATH)


def _run_preflight_tests(reportlooprunner, cfg: dict) -> None:
    """Test SharePoint and database connectivity at startup; write results to the logs."""
    logger.info('=== Pre-flight connectivity tests ===')

    # --- SharePoint ---
    if cfg.get('sharepoint_sync_enabled'):
        try:
            from API.clients.sharepoint import SharepointClient

            client = SharepointClient()
            token = client.get_access_token()
            if not token:
                raise RuntimeError('empty access token')
            library = client.get_document_library_by_name('AIMData')
            if library:
                logger.info(
                    'SharePoint: OK (token obtained, AIMData library id=%s)',
                    library.get('id'),
                )
            else:
                logger.warning('SharePoint: token OK but AIMData document library not found')
        except Exception as exc:
            logger.warning('SharePoint: FAILED - %s', exc)
    else:
        logger.info('SharePoint: skipped (sharepoint_sync_enabled=false)')

    # --- Databases ---
    settings = reportlooprunner.settings or {}
    databases = settings.get('databases', {}) if isinstance(settings, dict) else {}

    postgis_cfg = databases.get('PostGIS') if isinstance(databases, dict) else None
    if postgis_cfg:
        try:
            from lib.connectors.PostGISConnector import SinglePostGISConnector

            connector = SinglePostGISConnector.get_connector()
            conn = connector.pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute('SELECT 1')
                cur.fetchone()
                cur.close()
            finally:
                connector.pool.putconn(conn)
            logger.info(
                'PostGIS: OK (SELECT 1 succeeded on %s:%s/%s)',
                postgis_cfg.get('host'),
                postgis_cfg.get('port'),
                postgis_cfg.get('database'),
            )
        except Exception as exc:
            logger.warning('PostGIS: FAILED - %s', exc)
    else:
        logger.info('PostGIS: skipped (not configured)')

    neo4j_cfg = databases.get('Neo4j') if isinstance(databases, dict) else None
    if neo4j_cfg:
        try:
            from lib.connectors.Neo4JConnector import SingleNeo4JConnector

            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session(database=connector.db) as session:
                session.run('RETURN 1 AS test').single()
            logger.info(
                'Neo4j: OK (RETURN 1 succeeded on %s/%s)',
                neo4j_cfg.get('uri'),
                neo4j_cfg.get('database'),
            )
        except Exception as exc:
            logger.warning('Neo4j: FAILED - %s', exc)
    else:
        logger.info('Neo4j: skipped (not configured)')

    arango_cfg = databases.get('ArangoDB') if isinstance(databases, dict) else None
    if arango_cfg:
        try:
            from datasources.arango import SingleArangoConnector

            db = SingleArangoConnector.get_db()
            list(db.aql.execute('RETURN 1 AS test', max_runtime=10))
            logger.info(
                'ArangoDB: OK (RETURN 1 succeeded on %s:%s/%s)',
                arango_cfg.get('host'),
                arango_cfg.get('port'),
                arango_cfg.get('database'),
            )
        except Exception as exc:
            logger.warning('ArangoDB: FAILED - %s', exc)
    else:
        logger.info('ArangoDB: skipped (not configured)')

    pipeline_state_cfg = cfg.get('pipeline_state', {})
    if pipeline_state_cfg.get('enabled', True):
        db_path = pipeline_state_cfg.get('db_path', '')
        if db_path:
            try:
                from lib.connectors.pipeline_state import PipelineState

                ps = PipelineState(db_path)
                current = ps.get()
                logger.info(
                    'SQLite pipeline_state: OK (db_path=%s, current_state=%s)',
                    db_path,
                    current,
                )
            except Exception as exc:
                logger.warning('SQLite pipeline_state: FAILED - %s', exc)
        else:
            logger.info('SQLite pipeline_state: skipped (db_path empty)')
    else:
        logger.info('SQLite pipeline_state: skipped (disabled)')

    logger.info('=== Pre-flight connectivity tests complete ===')


if __name__ == '__main__':
    settings_path = _default_settings_path()
    cfg = _load_runtime_config(settings_path)
    onedrive_path = cfg['local_folder']

    _enable_daily_console_capture(onedrive_path)

    logger.info('Using settings: %s', settings_path)
    logger.info(
        'Runtime config: local_folder=%s, sharepoint_sync_enabled=%s, sharepoint_folder=%s, '
        'poll_after=%s, poll_deadline=%s',
        onedrive_path,
        cfg['sharepoint_sync_enabled'],
        cfg['sharepoint_folder'],
        cfg.get('drive_poll_after', '00:00:00'),
        cfg.get('drive_poll_deadline', '06:00:00'),
    )

    reportlooprunner = ReportLoopRunner(settings_path=cfg['settings_path'], excel_output_dir=onedrive_path)

    _run_preflight_tests(reportlooprunner, cfg)

    if cfg['sharepoint_sync_enabled']:
        pipeline_state = None
        pipeline_state_cfg = cfg.get('pipeline_state', {})
        if pipeline_state_cfg.get('enabled', True):
            db_path = pipeline_state_cfg.get('db_path', '')
            if db_path:
                from lib.connectors.pipeline_state import PipelineState
                pipeline_state = PipelineState(db_path)
                logger.info('PipelineState initialized with db_path=%s', db_path)
            else:
                logger.warning('pipeline_state enabled but db_path is empty; sharepoint gate will not poll SQLite.')
        else:
            logger.info('pipeline_state disabled; sharepoint gate will not poll SQLite.')

        sync_gate = DailySharePointSyncGate(
            local_folder=onedrive_path,
            drive_folder=cfg['sharepoint_folder'],
            token_path='',
            poll_start_hms=cfg.get('sharepoint_poll_after', '00:00:00'),
            hard_deadline_hms=cfg.get('sharepoint_poll_deadline', '06:00:00'),
            pipeline_state=pipeline_state,
        )
        reportlooprunner.on_before_run = sync_gate.ensure_synced
        reportlooprunner.on_run_complete = lambda: upload_after_run(
            local_folder=onedrive_path,
            drive_folder=cfg['sharepoint_folder'],
            token_path='',
            pipeline_state=pipeline_state,
        )
        logger.info('SharePoint sync gate and upload hooks attached to ReportLoopRunner.')

        if pipeline_state is not None:
            current = pipeline_state.get()
            if current and current.get('phase') == 'sharepoint_upload' and current.get('status') in ('starting', 'running', 'failed'):
                logger.info(
                    'Detected pending sharepoint_upload/%s from previous run; retrying upload before reports.',
                    current.get('status'),
                )
                try:
                    upload_after_run(
                        local_folder=onedrive_path,
                        drive_folder=cfg['sharepoint_folder'],
                        token_path='',
                        pipeline_state=pipeline_state,
                    )
                except Exception as exc:
                    logger.error(f'Upload retry failed: {exc}')
    elif cfg['sharepoint_sync_enabled']:
        logger.warning('SharePoint sync enabled in settings but unavailable; continuing without SharePoint sync hooks.')

    logger.info('Starting ReportLoopRunner (run_right_away=False).')
    reportlooprunner.start(run_right_away=False)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py