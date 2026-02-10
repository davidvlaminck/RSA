import argparse
import time
from datetime import datetime, UTC

from lib.reports.selection_runner import run_selection


DEFAULT_SETTINGS_PATH = r'/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'


def run_daily(settings_path: str, report: str) -> int:
    """Run a single report once per day using the shared selection runner."""
    started_running_date = None

    while True:
        now_utc = datetime.now(UTC)
        if started_running_date is None or started_running_date != now_utc.date():
            print(f'{now_utc}: let\'s run the report now')
            started_running_date = now_utc.date()
            return run_selection(settings_path=settings_path, report_names=[report], stream_output=True)

        print(f'{datetime.now(UTC)}: not yet the right time to run reports.')
        time.sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a single report (shared runner)')
    parser.add_argument('--settings', default=DEFAULT_SETTINGS_PATH)
    parser.add_argument('--report', default='Report0002')
    parser.add_argument('--once', action='store_true', help='Run once and exit')

    args = parser.parse_args()

    if args.once:
        raise SystemExit(run_selection(settings_path=args.settings, report_names=[args.report], stream_output=True))

    raise SystemExit(run_daily(args.settings, args.report))
