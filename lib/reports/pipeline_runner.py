"""Shared pipeline runner for datasource-parallel execution.

Runs one pipeline per datasource concurrently, each pipeline executes its report list
sequentially in a single worker subprocess.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, TextIO

from lib.reports.parallel_utils import group_reports_by_datasource

logger = logging.getLogger(__name__)


def _read_historical_durations(report_names: list[str], output_dir: Path | str) -> dict[str, float]:
    """Read historical query times from the Overzicht workbook column H.

    Returns a dict mapping report_name -> estimated_seconds.
    Reports not found or with missing/empty query times get float('inf') so they sort last.
    """
    try:
        from outputs.excel import ExcelOutput

        out_path = Path(output_dir)
        overview_path = out_path / 'Overzicht' / '[RSA] Overzicht rapporten.xlsx'
        if not overview_path.exists():
            return {rname: float('inf') for rname in report_names}

        excel = ExcelOutput(output_dir=str(out_path))
        rows = excel.read_data_from_sheet(str(overview_path), 'Overzicht')
        if not rows:
            return {rname: float('inf') for rname in report_names}

        durations: dict[str, float] = {}
        for row in rows:
            if len(row) > 7:
                report_name = row[5] if len(row) > 5 else None
                query_time = row[7] if len(row) > 7 else None
                if isinstance(report_name, str) and report_name.strip():
                    name = report_name.strip().lower()
                    if isinstance(query_time, (int, float)) and query_time > 0:
                        durations[name] = float(query_time)

        return {rname: durations.get(rname.lower(), float('inf')) for rname in report_names}
    except Exception:
        return {rname: float('inf') for rname in report_names}


def _sort_reports_by_duration(report_names: list[str], output_dir: Path | str) -> list[str]:
    """Sort reports by estimated query duration (ascending), unknowns last."""
    durations = _read_historical_durations(report_names, output_dir)
    return sorted(report_names, key=lambda rname: durations.get(rname, float('inf')))


def _stream_worker_output(output: str | None, stream: TextIO) -> None:
    """Write child output through Python's current stdout/stderr stream.

    ``subprocess.run(..., text=True)`` with inherited stdout writes to the
    process file descriptor and bypasses Python-level stream wrappers such as
    ``main.py``'s daily log tee. Piping the child output and writing it back to
    ``sys.stdout`` ensures terminal output is also captured in the run log.
    """

    if output:
        stream.write(output)
        stream.flush()


def _read_worker_status(status_file: str | None, expected_reports: list[str]) -> list[str] | None:
    """Read worker status file and return reports that did not complete successfully.

    Returns None if the status file is missing or unreadable (caller should fall back
    to treating all expected_reports as failed). Returns an empty list if all reports
    completed successfully.
    """
    if not status_file or not os.path.exists(status_file):
        return None

    completed = set()
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    report = entry.get('report')
                    if report == '__pipeline_done__':
                        continue
                    if entry.get('success'):
                        completed.add(report)
                except (json.JSONDecodeError, AttributeError):
                    continue
    except Exception:
        return None

    not_completed = [r for r in expected_reports if r not in completed]
    return not_completed


def _run_worker(report_names: list[str], settings_path: str, stream_output: bool,
                status_file: str | None = None, batch_size: int = 0,
                batch_timeout: float = 0, deadline: float = 0,
                process_holder: dict | None = None, process_timeout: float = 0) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "lib.reports.worker",
        "--reports",
        *report_names,
        "--settings",
        settings_path,
    ]
    if status_file:
        cmd.extend(["--status-file", status_file])
    if batch_size:
        cmd.extend(["--batch-size", str(batch_size)])
    if batch_timeout:
        cmd.extend(["--batch-timeout", str(batch_timeout)])
    if deadline:
        cmd.extend(["--deadline", str(deadline)])
    proc: subprocess.Popen[str] | None = None
    try:
        if stream_output:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                bufsize=1,
            )
            if process_holder is not None:
                process_holder['proc'] = proc
            output_chunks: list[str] = []
            start = time.time()
            while True:
                if process_timeout and (time.time() - start) > process_timeout:
                    logger.error(
                        "Worker hard timeout (%ss) exceeded, killing subprocess", process_timeout
                    )
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        pass
                    return {
                        "status": "timeout",
                        "error": f"hard timeout after {process_timeout}s",
                        "output": "".join(output_chunks),
                        "status_file": status_file,
                    }
                ret = proc.poll()
                if ret is not None:
                    for line in proc.stdout:
                        output_chunks.append(line)
                        _stream_worker_output(line, sys.stdout)
                    break
                line = proc.stdout.readline()
                if line:
                    output_chunks.append(line)
                    _stream_worker_output(line, sys.stdout)
            return {
                "status": "success" if proc.returncode == 0 else "error",
                "error": "Non-zero exit code",
                "output": "".join(output_chunks),
                "status_file": status_file,
            }
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
        if result.returncode == 0:
            return {"status": "success", "output": result.stdout or "", "status_file": status_file}
        return {"status": "error", "error": result.stdout or result.stderr or "Non-zero exit code", "output": result.stdout or "", "status_file": status_file}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "status_file": status_file}


def run_pipelines_by_datasource(
    report_names: Iterable[str],
    settings: dict,
    settings_path: str,
    *,
    stream_output: bool = True,
    timeout_seconds: int | None = None,
    batch_size: int = 10,
    batch_timeout: float = 0,
    deadline: float = 0,
) -> tuple[int, list[str]]:
    """Run pipelines per datasource concurrently.

    Args:
        report_names: List of report names to run.
        settings: Settings dictionary.
        settings_path: Path to settings file for worker processes.
        stream_output: Whether to stream output from worker processes.
        timeout_seconds: Kept for backward compatibility; not used for subprocess
            timeouts because per-report timeouts are now handled inside the worker.
        batch_size: Maximum reports per batch in each worker (default 10).
        batch_timeout: Maximum seconds per batch (0 = no batch timeout).
        deadline: Unix timestamp. When reached, workers stop executing.

    Returns:
        tuple: (return_code, failed_reports) where return_code is 0 on success, 1 if any pipeline fails or times out,
               and failed_reports is a list of report names that failed or timed out.
    """
    exec_cfg = settings.get("report_execution", {})
    max_concurrent = exec_cfg.get("max_concurrent", 2)

    groups = group_reports_by_datasource(list(report_names))
    pipelines = {ds: items for ds, items in groups.items() if items}
    if not pipelines:
        logger.info("No reports to run in parallel.")
        return 0, []

    drive_cfg = settings.get("drive_sync", {})
    excel_cfg = settings.get("output", {}).get("excel", {})
    output_dir = Path(drive_cfg.get("local_folder") or excel_cfg.get("output_dir") or "RSA_OneDrive")

    for datasource, report_list in pipelines.items():
        pipelines[datasource] = _sort_reports_by_duration(report_list, output_dir)
        logger.info("Sorted pipeline [%s] by estimated duration: %s", datasource, pipelines[datasource])

    max_workers = min(max_concurrent, len(pipelines))
    logger.info("Running %d pipelines in parallel (max_workers=%d)", len(pipelines), max_workers)

    failed: list[str] = []
    timed_out: list[str] = []
    status_files: list[str] = []

    # Calculate per-datasource overall timeout based on remaining deadline
    overall_timeout_per_datasource = None
    if deadline and time.time() < deadline:
        remaining = deadline - time.time()
        # Reserve half the remaining time for retries
        overall_timeout_per_datasource = remaining / 2
        logger.info(
            "Deadline in %.0fs, per-datasource overall timeout: %.0fs",
            remaining, overall_timeout_per_datasource,
        )

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pipeline = {}
            for datasource, report_list in pipelines.items():
                status_fd, status_file = tempfile.mkstemp(suffix='.jsonl', prefix='worker_status_')
                os.close(status_fd)
                status_files.append(status_file)
                logger.info("Starting pipeline [%s] with reports: %s", datasource, report_list)
                process_holder: dict = {}
                future = executor.submit(
                    _run_worker,
                    report_list,
                    settings_path,
                    stream_output,
                    status_file,
                    batch_size,
                    batch_timeout,
                    deadline,
                    process_holder,
                )
                future_to_pipeline[future] = (datasource, report_list, process_holder)

            for future in as_completed(future_to_pipeline):
                datasource, report_list, process_holder = future_to_pipeline[future]
                status_file = process_holder.get('status_file')
                try:
                    if overall_timeout_per_datasource:
                        result = future.result(timeout=overall_timeout_per_datasource)
                    else:
                        result = future.result()
                except TimeoutError:
                    proc = process_holder.get('proc')
                    if proc is not None and proc.poll() is None:
                        logger.warning("  [%s] pipeline exceeded overall timeout, killing worker", datasource)
                        try:
                            proc.kill()
                        except Exception:
                            pass
                        try:
                            proc.wait(timeout=5)
                        except Exception:
                            pass
                    actual_failed = _read_worker_status(status_file, report_list)
                    if actual_failed is None:
                        actual_failed = report_list
                    logger.warning("  [%s] pipeline timed out: %s (retrying %d reports)", datasource, report_list, len(actual_failed))
                    timed_out.extend(actual_failed)
                    continue
                except Exception as exc:
                    actual_failed = _read_worker_status(status_file, report_list)
                    if actual_failed is None:
                        actual_failed = report_list
                    logger.error("  [%s] pipeline error: %s - %s", datasource, report_list, exc)
                    failed.extend(actual_failed)
                    continue

                status_file = result.get("status_file")
                if result["status"] == "success":
                    logger.info("  [%s] pipeline completed: %s", datasource, report_list)
                elif result["status"] == "timeout":
                    actual_failed = _read_worker_status(status_file, report_list)
                    if actual_failed is None:
                        actual_failed = report_list
                    logger.warning("  [%s] pipeline timed out: %s (retrying %d reports)", datasource, report_list, len(actual_failed))
                    timed_out.extend(actual_failed)
                else:
                    actual_failed = _read_worker_status(status_file, report_list)
                    if actual_failed is None:
                        actual_failed = report_list
                    output = result.get("output", "")
                    if output:
                        logger.error(
                            "  [%s] pipeline failed: %s - %s\nOutput:\n%s",
                            datasource, report_list, result.get("error", "Unknown"), output,
                        )
                    else:
                        logger.error(
                            "  [%s] pipeline failed: %s - %s",
                            datasource, report_list, result.get("error", "Unknown"),
                        )
                    failed.extend(actual_failed)
    finally:
        for status_file in status_files:
            try:
                os.unlink(status_file)
            except Exception:
                pass

    if failed or timed_out:
        logger.warning("Summary:")
        if failed:
            logger.error("  Failed: %s", failed)
        if timed_out:
            logger.warning("  Timed out: %s", timed_out)
        return 1, failed + timed_out
    return 0, []
