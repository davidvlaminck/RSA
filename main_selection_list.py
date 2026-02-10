"""Run a fixed selection of reports via the worker CLI.

Defaults to the same settings file as main.py.
Supports overrides for settings path and report list.
"""
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.reports.parallel_utils import group_reports_by_datasource, create_balanced_batches


DEFAULT_SETTINGS_PATH = r"/home/davidlinux/Documenten/AWV/resources/settings_RSA.json"
DEFAULT_REPORTS = [
    "Report0002",
    "Report0004",
    "Report0030",
    "Report0048",
]


def build_command(settings_path: str, reports: list[str]) -> list[str]:
    return [
        "python",
        "-m",
        "lib.reports.worker",
        "--reports",
        *reports,
        "--settings",
        settings_path,
    ]


def run_worker(report_names: list[str], settings_path: str, timeout_seconds: int, stream_output: bool = True) -> dict:
    cmd = [
        "python",
        "-m",
        "lib.reports.worker",
        "--reports",
        *report_names,
        "--settings",
        settings_path,
    ]
    try:
        if stream_output:
            result = subprocess.run(
                cmd,
                timeout=timeout_seconds,
                text=True,
            )
        else:
            result = subprocess.run(
                cmd,
                timeout=timeout_seconds,
                capture_output=True,
                text=True,
            )
        if result.returncode == 0:
            return {"status": "success"}
        if stream_output:
            return {"status": "error", "error": "Non-zero exit code"}
        return {"status": "error", "error": result.stderr or "Non-zero exit code"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def run_parallel(settings_path: str, reports: list[str], max_concurrent: int, timeout_seconds: int) -> int:
    # Group reports by datasource and run one pipeline per datasource concurrently.
    groups = group_reports_by_datasource(reports)

    failed = []
    timed_out = []

    # Only keep groups that have reports.
    pipelines = {ds: items for ds, items in groups.items() if items}
    if not pipelines:
        print("No reports to run in parallel.")
        return 0

    # Limit to max_concurrent pipelines (2 for 8GB RAM).
    max_workers = min(max_concurrent, len(pipelines))
    print(f"Running {len(pipelines)} pipelines in parallel (max_workers={max_workers})")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pipeline = {}
        for datasource, report_list in pipelines.items():
            # Give each pipeline a timeout proportional to report count.
            pipeline_timeout = max(timeout_seconds, timeout_seconds * len(report_list))
            print(f"Starting pipeline [{datasource}] with reports: {report_list}")
            future = executor.submit(run_worker, report_list, settings_path, pipeline_timeout, True)
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
                print(f"  ✗ [{datasource}] pipeline failed: {report_list} - {result.get('error', 'Unknown')}")
                failed.extend(report_list)

    if failed or timed_out:
        print("\nSummary:")
        if failed:
            print(f"  Failed: {failed}")
        if timed_out:
            print(f"  Timed out: {timed_out}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a selected list of reports via the worker")
    parser.add_argument(
        "--settings",
        default=DEFAULT_SETTINGS_PATH,
        help="Path to settings JSON (defaults to main.py settings)",
    )
    parser.add_argument(
        "--reports",
        nargs="+",
        default=DEFAULT_REPORTS,
        help="Report names to run (space-separated)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run reports in parallel by datasource using settings.json limits",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command without executing it",
    )

    args = parser.parse_args()

    # Load settings to determine execution mode
    with open(args.settings, "r") as f:
        settings = json.load(f)

    exec_cfg = settings.get("report_execution", {})
    mode = exec_cfg.get("mode", "sequential")

    # Use parallel mode if --parallel flag is set OR if settings.json has parallel_by_datasource mode
    use_parallel = args.parallel or mode == "parallel_by_datasource"

    if use_parallel:
        max_concurrent = exec_cfg.get("max_concurrent", 2)
        timeout_seconds = exec_cfg.get("timeout_seconds", 1800)
        if args.dry_run:
            print(f"Parallel mode: max_concurrent={max_concurrent}, timeout_seconds={timeout_seconds}")
            print(f"Reports: {args.reports}")
            return 0
        print(f"Running in parallel mode (max_concurrent={max_concurrent}, timeout={timeout_seconds}s)")
        return run_parallel(args.settings, args.reports, max_concurrent, timeout_seconds)

    # Sequential mode
    cmd = build_command(args.settings, args.reports)

    if args.dry_run:
        print(" ".join(cmd))
        return 0

    print(f"Running in sequential mode")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
