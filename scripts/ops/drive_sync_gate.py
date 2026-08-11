from __future__ import annotations

import logging
from datetime import datetime, timezone

from lib.sqlite_queue_client import enqueue_sqlite_job

logger = logging.getLogger(__name__)


class DailyDriveSyncGate:
    """Polls SQLite for an external orchestrator's drive-download signal.

    The gate no longer performs the Drive download itself. It only observes
    ``pipeline_state`` for ``drive_download`` / ``completed``. Polling starts
    at ``poll_start_hms`` and is abandoned at ``hard_deadline_hms``, after
    which reports are allowed to proceed anyway.
    """

    def __init__(
        self,
        local_folder: str,
        drive_folder: str,
        token_path: str,
        poll_start_hms: str = '00:30:00',
        hard_deadline_hms: str = '06:00:00',
        pipeline_state=None,
    ):
        self.local_folder = local_folder
        self.drive_folder = drive_folder
        self.token_path = token_path
        self.poll_start_seconds = self._parse_hms(poll_start_hms)
        self.hard_deadline_seconds = self._parse_hms(hard_deadline_hms)
        self._synced_date = None
        self.pipeline_state = pipeline_state

        logger.info(
            '[DRIVE_SYNC_GATE] Initialized: poll_start=%s, hard_deadline=%s, local_folder=%s, drive_folder=%s',
            poll_start_hms,
            hard_deadline_hms,
            local_folder,
            drive_folder,
        )

    @staticmethod
    def _parse_hms(hms: str) -> int:
        hh, mm, ss = (int(part) for part in hms.split(':'))
        return hh * 3600 + mm * 60 + ss

    @staticmethod
    def _format_hms(total_seconds: int) -> str:
        hh = total_seconds // 3600
        mm = (total_seconds % 3600) // 60
        ss = total_seconds % 60
        return f'{hh:02d}:{mm:02d}:{ss:02d}'

    def _enqueue_pipeline_update(self, phase: str, status: str, message: str) -> None:
        if self.pipeline_state is not None and getattr(self.pipeline_state, 'db_path', ''):
            enqueue_sqlite_job('update_pipeline_state', {
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'phase': phase,
                'status': status,
                'message': message,
            })

    def ensure_synced(self, now: datetime) -> bool:
        if self._synced_date == now.date():
            logger.debug('[DRIVE_SYNC_GATE] Already synced today (%s).', now.date())
            return True

        now_seconds = now.hour * 3600 + now.minute * 60 + now.second
        logger.debug(
            '[DRIVE_SYNC_GATE] Checking sync for %s at %02d:%02d:%02d (poll_start=%s, hard_deadline=%s)',
            now.date(), now.hour, now.minute, now.second,
            self._format_hms(self.poll_start_seconds),
            self._format_hms(self.hard_deadline_seconds),
        )

        if now_seconds < self.poll_start_seconds:
            wait_seconds = self.poll_start_seconds - now_seconds
            logger.info(
                '[DRIVE_SYNC_GATE] Too early (%02d:%02d:%02d). Waiting %d seconds until poll window opens at %s.',
                now.hour, now.minute, now.second,
                wait_seconds,
                self._format_hms(self.poll_start_seconds),
            )
            return False

        if now_seconds >= self.hard_deadline_seconds:
            logger.warning(
                '[DRIVE_SYNC_GATE] Hard deadline (%s) reached without external confirmation. '
                'Proceeding with reports.',
                self._format_hms(self.hard_deadline_seconds),
            )
            self._synced_date = now.date()
            return True

        if self.pipeline_state is not None and getattr(self.pipeline_state, 'db_path', ''):
            current = self.pipeline_state.get()
            if current and current.get('phase') == 'drive_download' and current.get('status') == 'completed':
                self._synced_date = now.date()
                logger.info(
                    '[DRIVE_SYNC_GATE] External orchestrator confirmed drive_download completed. '
                    'Reports can proceed.'
                )
                return True
            if current and current.get('phase') == 'drive_download' and current.get('status') == 'starting':
                self._enqueue_pipeline_update(
                    'drive_download', 'running',
                    'Waiting for external orchestrator to complete drive download',
                )
                logger.info(
                    '[DRIVE_SYNC_GATE] External orchestrator started drive_download. Waiting for completion...'
                )
                return False

            if current and current.get('phase') != 'drive_download':
                self._synced_date = now.date()
                logger.info(
                    '[DRIVE_SYNC_GATE] Pipeline state is %s (not drive_download); '
                    'treating drive sync as already completed.',
                    current.get('phase'),
                )
                return True

            self._enqueue_pipeline_update(
                'drive_download', 'running',
                'Waiting for external orchestrator to start drive download',
            )
            logger.info(
                '[DRIVE_SYNC_GATE] Waiting for external orchestrator to start drive_download. '
                'Current state: %s',
                current if current else 'no state yet',
            )
            return False

        self._synced_date = now.date()
        return True


def upload_after_run(local_folder: str, drive_folder: str, token_path: str, pipeline_state=None) -> None:
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

        enqueue_sqlite_job('update_pipeline_state', {
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'phase': 'drive_upload',
            'status': 'running',
            'message': f'drive_folder={drive_folder}',
        })

    from scripts.ops.gdrive_upload import sync_local_to_drive, write_daily_run_log

    write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_START', f'drive_folder={drive_folder}')
    ok = sync_local_to_drive(
        local_folder=local_folder,
        drive_folder_name=drive_folder,
        token_path=token_path,
    )
    if ok:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_DONE', f'drive_folder={drive_folder}')
        if pipeline_state is not None:
            enqueue_sqlite_job('update_pipeline_state', {
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'phase': 'drive_upload',
                'status': 'completed',
                'message': f'drive_folder={drive_folder}',
            })
    else:
        write_daily_run_log(local_folder, 'POST_RUN_UPLOAD_FAILED', f'drive_folder={drive_folder}')
        if pipeline_state is not None:
            enqueue_sqlite_job('update_pipeline_state', {
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'phase': 'drive_upload',
                'status': 'failed',
                'message': f'drive_folder={drive_folder}',
            })