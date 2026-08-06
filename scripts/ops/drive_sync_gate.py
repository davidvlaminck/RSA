from __future__ import annotations

import logging
from datetime import datetime

from scripts.ops.gdrive_upload import (
    sync_drive_to_local,
    sync_local_to_drive,
    validate_local_mirror,
    write_daily_run_log,
)

logger = logging.getLogger(__name__)


class DailyDriveSyncGate:
    """Ensures one Drive->local sync is completed each day before reports can run."""

    def __init__(self, local_folder: str, drive_folder: str, token_path: str, earliest_sync_hms: str = '01:00:00', pipeline_state=None):
        self.local_folder = local_folder
        self.drive_folder = drive_folder
        self.token_path = token_path
        self.earliest_sync_seconds = self._parse_hms(earliest_sync_hms)
        self._synced_date = None
        self.pipeline_state = pipeline_state

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

        # Orchestrator-driven: wacht tot pipeline_state = drive_download / starting
        if self.pipeline_state is not None and getattr(self.pipeline_state, 'db_path', ''):
            current = self.pipeline_state.get()
            if current and current.get('phase') == 'drive_download' and current.get('status') == 'completed':
                self._synced_date = now.date()
                return True
            if not (current and current.get('phase') == 'drive_download' and current.get('status') == 'starting'):
                return False

        write_daily_run_log(self.local_folder, 'PRE_SYNC_START', f'drive_folder={self.drive_folder}')
        if self.pipeline_state is not None and getattr(self.pipeline_state, 'db_path', ''):
            self.pipeline_state.update('drive_download', 'running', f'drive_folder={self.drive_folder}')
        ok = sync_drive_to_local(
            local_folder=self.local_folder,
            drive_folder_name=self.drive_folder,
            token_path=self.token_path,
        )
        if ok:
            valid, reason = validate_local_mirror(self.local_folder)
            if not valid:
                write_daily_run_log(self.local_folder, 'PRE_SYNC_INVALID_MIRROR', reason)
                if self.pipeline_state is not None:
                    self.pipeline_state.update('drive_download', 'failed', reason)
                logger.warning('[SYNC] Invalid local mirror after sync-down: %s', reason)
                return False
            self._synced_date = now.date()
            write_daily_run_log(self.local_folder, 'PRE_SYNC_DONE', f'drive_folder={self.drive_folder}')
            if self.pipeline_state is not None:
                self.pipeline_state.update('drive_download', 'completed', f'drive_folder={self.drive_folder}')
        else:
            write_daily_run_log(self.local_folder, 'PRE_SYNC_FAILED', f'drive_folder={self.drive_folder}')
            if self.pipeline_state is not None:
                self.pipeline_state.update('drive_download', 'failed', f'drive_folder={self.drive_folder}')

        return ok


def upload_after_run(local_folder: str, drive_folder: str, token_path: str, pipeline_state=None) -> None:
    # Orchestrator-driven: wacht tot pipeline_state = drive_upload / starting
    if pipeline_state is not None and getattr(pipeline_state, 'db_path', ''):
        import time
        timeout = 3600
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = pipeline_state.get()
            if current and current.get('phase') == 'drive_upload' and current.get('status') == 'starting':
                break
            time.sleep(30)
        else:
            logger.warning('[UPLOAD] Timeout waiting for drive_upload/starting signal; proceeding with upload anyway.')
        pipeline_state.update('drive_upload', 'running', f'drive_folder={drive_folder}')

    write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_START', f'drive_folder={drive_folder}')
    ok = sync_local_to_drive(
        local_folder=local_folder,
        drive_folder_name=drive_folder,
        token_path=token_path,
    )
    if ok:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_DONE', f'drive_folder={drive_folder}')
        if pipeline_state is not None:
            pipeline_state.update('drive_upload', 'completed', f'drive_folder={drive_folder}')
    else:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_FAILED', f'drive_folder={drive_folder}')
        if pipeline_state is not None:
            pipeline_state.update('drive_upload', 'failed', f'drive_folder={drive_folder}')