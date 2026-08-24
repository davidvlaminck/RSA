from __future__ import annotations

import logging
from datetime import datetime, timezone

from lib.connectors.pipeline_state import enqueue_sqlite_job

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
        poll_start_hms: str = '00:00:00',
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

    def _check_pipeline_state(self, now: datetime) -> tuple[bool, bool]:
        """Check SQLite pipeline_state.

        Returns:
            (should_proceed, should_retry_upload)
            - should_proceed: True if the gate should allow the run to proceed
              (either because drive_download is done, or because the cycle is
              already complete and _should_run_rsa_queries() will block it).
            - should_retry_upload: True if a pending upload should be retried.
        """
        if self.pipeline_state is None or not getattr(self.pipeline_state, 'db_path', ''):
            return False, False

        current = self.pipeline_state.get()
        if not current:
            return False, False

        phase = current.get('phase', '')
        status = current.get('status', '')

        if phase == 'drive_upload':
            if status in ('starting', 'running'):
                return False, True
            if status == 'failed':
                return False, True
            if status == 'completed':
                return True, False

        if phase == 'rsa_queries' and status in ('completed', 'time-out'):
            return True, False

        # If the pipeline has already advanced past drive_download into later
        # phases (e.g. rsa_queries running, postgis sync phases), the download
        # has already completed. Don't block reports waiting for a
        # drive_download signal that already came and went.
        if phase in (
            'arango_sync',
            'postgis_sync_pausing',
            'postgis_sync_paused',
            'postgis_sync_running',
            'postgis_sync_resuming',
            'rsa_queries',
        ):
            self._synced_date = now.date()
            return True, False

        if phase == 'drive_download' and status == 'completed':
            self._synced_date = now.date()
            return True, False

        if phase == 'drive_download' and status == 'starting':
            self._enqueue_pipeline_update(
                'drive_download', 'running',
                'Waiting for external orchestrator to complete drive download',
            )
            return False, False

        return False, False

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

        should_proceed, should_retry_upload = self._check_pipeline_state(now)
        if should_retry_upload:
            logger.info(
                '[DRIVE_SYNC_GATE] Detected pending %s/%s; will retry upload before reports.',
                current.get('phase'), current.get('status'),
            )
            return False
        if should_proceed:
            return True

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
            logger.info(
                '[DRIVE_SYNC_GATE] Pipeline state is %s (not drive_download); waiting for drive_download to appear.',
                current.get('phase') if current else 'no state yet',
            )
        else:
            logger.info(
                '[DRIVE_SYNC_GATE] No pipeline_state configured; waiting until hard deadline or drive_download signal.'
            )

        return False


def upload_after_run(local_folder: str, drive_folder: str, token_path: str, pipeline_state=None) -> None:
    if pipeline_state is not None and getattr(pipeline_state, 'db_path', ''):
        import time
        timeout = 3600
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = pipeline_state.get()
            if current and current.get('phase') == 'drive_upload' and current.get('status') in ('starting', 'running', 'failed'):
                break
            time.sleep(30)
        else:
            logger.warning('[UPLOAD] Timeout waiting for drive_upload signal; proceeding with upload anyway.')

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