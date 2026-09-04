"""Force the pipeline state to allow RSA queries to run immediately.

Use case: the orchestrator that normally drives postgis_sync has not signalled
yet (or crashed before it could), and the RSA runner is stuck in the 4am-7am
passive wait. Running this script once queues the right state transition so
the next run of main.py will proceed.

Safe to run repeatedly: each call queues a fresh job that just resets the
state to the desired phase. Existing jobs already in the queue are not
disturbed.

The script injects its own repo root onto ``sys.path`` so it runs equally well
under plain ``python`` (PyCharm Play), ``uv run`` (no PYTHONPATH needed) or as
a one-off ``/usr/bin/python3 scripts/ops/force_run_reports.py``.
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root is importable no matter how the script is launched.
_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]  # scripts/ops/force_run_reports.py -> RSA/
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from lib.connectors.pipeline_state import enqueue_sqlite_job  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--db-path",
        default=os.environ.get(
            "RSA_PIPELINE_DB",
            "/opt/data-platform/RSA_Health/health.db",
        ),
        help="Path to the pipeline state SQLite (default: env RSA_PIPELINE_DB or the production path)",
    )
    p.add_argument(
        "--phase",
        default="postgis_sync_paused",
        choices=[
            "postgis_sync_paused",
            "postgis_sync_running",
            "postgis_sync_resuming",
            "rsa_queries",
        ],
        help="Which phase to signal (default: postgis_sync_paused, which the runner accepts)",
    )
    p.add_argument(
        "--message",
        default="Manually forced from scripts/force_run_reports.py",
        help="Free-text message stored alongside the state",
    )
    args = p.parse_args()

    print(f"Queueing pipeline state: phase={args.phase} db={args.db_path}")
    job_id = enqueue_sqlite_job(
        "update_pipeline_state",
        {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "phase": args.phase,
            "status": "running",
            "message": args.message,
        },
    )
    print(f"Queued job_id={job_id}")
    print("The next run of main.py will pick this up within ~60s polling interval.")


if __name__ == "__main__":
    main()