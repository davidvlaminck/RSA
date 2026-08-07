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
from scripts.ops.gdrive_upload import (
    sync_drive_to_local,
    sync_local_to_drive,
    validate_local_mirror,
    write_daily_run_log,
    prune_daily_run_logs,
)

logger = logging.getLogger(__name__)


DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent / 'settings_RSA.json'
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

    local_folder_raw = drive_cfg.get('local_folder') or excel_cfg.get('output_dir') or 'RSA_OneDrive'

    return {
        'settings_path': settings_path,
        'local_folder': _resolve_path(local_folder_raw, settings_dir),
        'drive_sync_enabled': bool(drive_cfg.get('enabled', True)),
        'drive_sync_after': drive_cfg.get('sync_after', '01:00:00'),
        'drive_folder': drive_cfg.get('drive_folder', 'RSA'),
        'token_path': drive_cfg.get('token_path', ''),
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

    reportlooprunner = ReportLoopRunner(settings_path=cfg['settings_path'], excel_output_dir=onedrive_path)

    if cfg['drive_sync_enabled'] and cfg['token_path']:
        pipeline_state = None
        pipeline_state_cfg = cfg.get('pipeline_state', {})
        if pipeline_state_cfg.get('enabled', True):
            db_path = pipeline_state_cfg.get('db_path', '')
            if db_path:
                from lib.connectors.pipeline_state import PipelineState
                pipeline_state = PipelineState(db_path)

        sync_gate = DailyDriveSyncGate(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
            earliest_sync_hms=cfg['drive_sync_after'],
            pipeline_state=pipeline_state,
        )
        reportlooprunner.on_before_run = sync_gate.ensure_synced
        reportlooprunner.on_run_complete = lambda: upload_after_run(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
            pipeline_state=pipeline_state,
        )
    elif cfg['drive_sync_enabled']:
        logger.warning('Drive sync enabled in settings but token_path is empty; continuing without Drive sync hooks.')

    # With scheduled flow, let settings.time control when reports start (e.g. around 06:00).
    reportlooprunner.start(run_right_away=False)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py