from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from lib.reports.ReportLoopRunner import ReportLoopRunner
from scripts.ops.gdrive_upload import (
    sync_drive_to_local,
    sync_local_to_drive,
    write_daily_run_log,
)


DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent / 'settings_sample.json'


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


class DailyDriveSyncGate:
    """Ensures one Drive->local sync is completed each day before reports can run."""

    def __init__(self, local_folder: str, drive_folder: str, token_path: str, earliest_sync_hms: str = '01:00:00'):
        self.local_folder = local_folder
        self.drive_folder = drive_folder
        self.token_path = token_path
        self.earliest_sync_seconds = self._parse_hms(earliest_sync_hms)
        self._synced_date = None

    @staticmethod
    def _parse_hms(hms: str) -> int:
        hh, mm, ss = (int(part) for part in hms.split(':'))
        return hh * 3600 + mm * 60 + ss

    def ensure_synced(self, now: datetime) -> bool:
        if self._synced_date == now.date():
            return True

        now_seconds = now.hour * 3600 + now.minute * 60 + now.second
        if now_seconds < self.earliest_sync_seconds:
            return False

        write_daily_run_log(self.local_folder, 'PRE_SYNC_START', f'drive_folder={self.drive_folder}')
        ok = sync_drive_to_local(
            local_folder=self.local_folder,
            drive_folder_name=self.drive_folder,
            token_path=self.token_path,
        )
        if ok:
            self._synced_date = now.date()
            write_daily_run_log(self.local_folder, 'PRE_SYNC_DONE', f'drive_folder={self.drive_folder}')
        else:
            write_daily_run_log(self.local_folder, 'PRE_SYNC_FAILED', f'drive_folder={self.drive_folder}')

        return ok


def upload_after_run(local_folder: str, drive_folder: str, token_path: str) -> None:
    write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_START', f'drive_folder={drive_folder}')
    ok = sync_local_to_drive(
        local_folder=local_folder,
        drive_folder_name=drive_folder,
        token_path=token_path,
    )
    if ok:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_DONE', f'drive_folder={drive_folder}')
    else:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_FAILED', f'drive_folder={drive_folder}')


if __name__ == '__main__':
    settings_path = _default_settings_path()
    cfg = _load_runtime_config(settings_path)
    onedrive_path = cfg['local_folder']

    print(f'Using settings: {settings_path}')

    reportlooprunner = ReportLoopRunner(settings_path=cfg['settings_path'], excel_output_dir=onedrive_path)

    if cfg['drive_sync_enabled'] and cfg['token_path']:
        sync_gate = DailyDriveSyncGate(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
            earliest_sync_hms=cfg['drive_sync_after'],
        )
        reportlooprunner.on_before_run = sync_gate.ensure_synced
        reportlooprunner.on_run_complete = lambda: upload_after_run(
            local_folder=onedrive_path,
            drive_folder=cfg['drive_folder'],
            token_path=cfg['token_path'],
        )
    elif cfg['drive_sync_enabled']:
        print('Drive sync enabled in settings but token_path is empty; continuing without Drive sync hooks.')

    # With scheduled flow, let settings.time control when reports start (e.g. around 06:00).
    reportlooprunner.start(run_right_away=False)

# first on linux do: pip install psycopg2-binary

# bash script for VM
# #! usr/bin/bash
# # sleep 5h (possibly)
# export PYTHONPATH=/home/david/PycharmProjects/RSA:$PYTHONPATH
# ~/PycharmProjects/RSA/venv314/bin/python3.14 ~/PycharmProjects/RSA/main.py