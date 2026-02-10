"""Shared pipeline runner for datasource-parallel execution.

Runs one pipeline per datasource concurrently, each pipeline executes its report list
sequentially in a single worker subprocess.
"""
from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from lib.reports.parallel_utils import group_reports_by_datasource


def _run_worker(report_names: list[str], settings_path: str, timeout_seconds: int, stream_output: bool) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "lib.reports.worker",
        "--reports",
        *report_names,
        "--settings",
        settings_path,
    ]
    try:
        if stream_output:
            result = subprocess.run(cmd, timeout=timeout_seconds, text=True)
        else:
            result = subprocess.run(cmd, timeout=timeout_seconds, capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success"}
        if stream_output:
            return {"status": "error", "error": "Non-zero exit code"}
        return {"status": "error", "error": result.stderr or "Non-zero exit code"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def run_pipelines_by_datasource(
    report_names: Iterable[str],
    settings: dict,
    settings_path: str,
    *,
    stream_output: bool = True,
) -> int:
    """Run pipelines per datasource concurrently.

    Returns 0 on success, 1 if any pipeline fails or times out.
    """
    exec_cfg = settings.get("report_execution", {})
    max_concurrent = exec_cfg.get("max_concurrent", 2)
    timeout_seconds = exec_cfg.get("timeout_seconds", 1800)

    groups = group_reports_by_datasource(list(report_names))
    pipelines = {ds: items for ds, items in groups.items() if items}
    if not pipelines:
        print("No reports to run in parallel.")
        return 0

    max_workers = min(max_concurrent, len(pipelines))
    print(f"Running {len(pipelines)} pipelines in parallel (max_workers={max_workers})")

    failed: list[str] = []
    timed_out: list[str] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pipeline = {}
        for datasource, report_list in pipelines.items():
            pipeline_timeout = max(timeout_seconds, timeout_seconds * len(report_list))
            print(f"Starting pipeline [{datasource}] with reports: {report_list}")
            future = executor.submit(
                _run_worker,
                report_list,
                settings_path,
                pipeline_timeout,
                stream_output,
            )
            future_to_pipeline[future] = (datasource, report_list)

        for future in as_completed(future_to_pipeline):
            datasource, report_list = future_to_pipeline[future]
            result = future.result()
            if result["status"] == "success":
                print(f"  ✓ [{datasource}] pipeline completed: {report_list}")
            elif result["status"] == "timeout":
                print(f"  ⏱ [{datasource}] pipeline timed out: {report_list}")
                timed_out.extend(report_list)
            else:
                print(
                    f"  ✗ [{datasource}] pipeline failed: {report_list} - "
                    f"{result.get('error', 'Unknown')}"
                )
                failed.extend(report_list)

    if failed or timed_out:
        print("\nSummary:")
        if failed:
            print(f"  Failed: {failed}")
        if timed_out:
            print(f"  Timed out: {timed_out}")
        return 1
    return 0
