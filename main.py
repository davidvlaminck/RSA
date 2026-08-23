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
from scripts.ops.drive_sync_gate import DailyDriveSyncGate, upload_after_run
from scripts.ops.gdrive_upload import prune_daily_run_logs

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
    drive_cfg = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
    output_cfg = settings.get('output', {}) if isinstance(settings, dict) else {}
    excel_cfg = output_cfg.get('excel', {}) if isinstance(output_cfg, dict) else {}
    pipeline_state_cfg = settings.get('pipeline_state', {}) if isinstance(settings, dict) else {}

    local_folder_raw = drive_cfg.get('local_folder') or excel_cfg.get('output_dir') or 'RSA_OneDrive'
    pipeline_state_raw = pipeline_state_cfg.get('db_path', '')

    return {
        'settings_path': settings_path,
        'local_folder': _resolve_path(local_folder_raw, settings_dir),
        'drive_sync_enabled': bool(drive_cfg.get('enabled', True)),
        'drive_sync_after': drive_cfg.get('sync_after', '01:00:00'),
        'drive_folder': drive_cfg.get('drive_folder', 'RSA'),
        'token_path': drive_cfg.get('token_path', ''),
        'drive_poll_after': drive_cfg.get('poll_after', '00:30:00'),
        'drive_poll_deadline': drive_cfg.get('poll_deadline', '06:00:00'),
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


if __name__ == '__main__':
    settings_path = _default_settings_path()
    cfg = _load_runtime_config(settings_path)
    onedrive_path = cfg['local_folder']

    _enable_daily_console_capture(onedrive_path)

    logger.info('Using settings: %s', settings_path)
    logger.info(
        'Runtime config: local_folder=%s, drive_sync_enabled=%s, drive_folder=%s, '
        'poll_after=%s, poll_deadline=%s',
        onedrive_path,
        cfg['drive_sync_enabled'],
        cfg['drive_folder'],
        cfg.get('drive_poll_after', '00:00:00'),
        cfg.get('drive_poll_deadline', '06:00:00'),
    )

    reportlooprunner = ReportLoopRunner(settings_path=cfg['settings_path'], excel_output_dir=onedrive_path)

    if cfg['drive_sync_enabled'] and cfg['token_path']:
        pipeline_state = None
        pipeline_state_cfg = cfg.get('pipeline_state', {})
        if pipeline_state_cfg.get('enabled', True):
            db_path = pipeline_state_cfg.get('db_path', '')
            if db_path:
                from lib.connectors.pipeline_state import PipelineState
                pipeline_state = PipelineState(db_path)
                logger.info('PipelineState initialized with db_path=%s', db_path)
            else:
                logger.warning('pipeline_state enabled but db_path is empty; drive gate will not poll SQLite.')
        else:
            logger.info('pipeline_state disabled; drive gate will not poll SQLite.')

        sync_gate = DailyDriveSyncGate(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
            poll_start_hms=cfg.get('drive_poll_after', '00:00:00'),
            hard_deadline_hms=cfg.get('drive_poll_deadline', '06:00:00'),
            pipeline_state=pipeline_state,
        )
        reportlooprunner.on_before_run = sync_gate.ensure_synced
        reportlooprunner.on_run_complete = lambda: upload_after_run(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
            pipeline_state=pipeline_state,
        )
        logger.info('Drive sync gate and upload hooks attached to ReportLoopRunner.')

        if pipeline_state is not None:
            current = pipeline_state.get()
            if current and current.get('phase') == 'drive_upload' and current.get('status') in ('starting', 'running', 'failed'):
                logger.info(
                    'Detected pending drive_upload/%s from previous run; retrying upload before reports.',
                    current.get('status'),
                )
                try:
                    upload_after_run(
                        local_folder=onedrive_path,
                        drive_folder=cfg['drive_folder'],
                        token_path=cfg['token_path'],
                        pipeline_state=pipeline_state,
                    )
                except Exception as exc:
                    logger.error(f'Upload retry failed: {exc}')
    elif cfg['drive_sync_enabled']:
        logger.warning('Drive sync enabled in settings but token_path is empty; continuing without Drive sync hooks.')

    logger.info('Starting ReportLoopRunner (run_right_away=False).')
    reportlooprunner.start(run_right_away=False)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py