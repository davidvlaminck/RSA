"""Run a fixed selection of reports via the worker CLI.

Defaults to the same settings file as main.py.
Supports overrides for settings path and report list.
"""

import argparse

from lib.reports.selection_runner import run_selection


DEFAULT_SETTINGS_PATH = r"/home/davidlinux/Documenten/AWV/resources/settings_RSA.json"
DEFAULT_REPORTS = [
    "Report0002",
    "Report0004",
    "Report0030",
    "Report0048",
]


def _print_dry_run(settings_path: str, reports: list[str], use_parallel: bool):
    mode = "parallel" if use_parallel else "sequential"
    print(f"Mode: {mode}")
    print(f"Settings: {settings_path}")
    print(f"Reports: {reports}")


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

    # Use parallel mode if --parallel flag is set; otherwise follow settings.json
    use_parallel = args.parallel or None

    if args.dry_run:
        _print_dry_run(args.settings, args.reports, bool(use_parallel))
        return 0

    return run_selection(
        settings_path=args.settings,
        report_names=args.reports,
        force_parallel=use_parallel,
        stream_output=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
