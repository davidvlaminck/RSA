#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.mail.archive_mailer import zip_and_mail_output_dir
from lib.reports.ReportLoopRunner import ReportLoopRunner


DEFAULT_SETTINGS = '/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'
DEFAULT_REPORT = 'Report0002'
DEFAULT_RECIPIENT = 'david.vlaminck@mow.vlaanderen.be'
DEFAULT_OUTPUT_DIR = str(repo_root / 'RSA_OneDrive')


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run one report to Excel, then zip the output folder and mail it.'
    )
    parser.add_argument('--settings', default=DEFAULT_SETTINGS, help='Path to settings JSON')
    parser.add_argument('--report', default=DEFAULT_REPORT, help='Report class name to run')
    parser.add_argument('--output-dir', default=DEFAULT_OUTPUT_DIR, help='Excel output directory')
    parser.add_argument('--recipient', default=DEFAULT_RECIPIENT, help='Archive recipient email')
    parser.add_argument('--keep-archive', action='store_true', help='Keep the generated zip after mailing')
    parser.add_argument(
        '--send-report-mails',
        action='store_true',
        help='Also send the normal report mails; by default they are suppressed for this test flow.',
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = ReportLoopRunner(settings_path=args.settings, excel_output_dir=str(output_dir))
    runner.output_type = 'Excel'
    if isinstance(runner.settings, dict):
        runner.settings.setdefault('output', {})
        runner.settings['output']['type'] = 'Excel'
        runner.settings['output'].setdefault('excel', {})
        runner.settings['output']['excel']['output_dir'] = str(output_dir)
        runner.output_settings = runner.settings['output']

    if not args.send_report_mails:
        runner.mail_sender.send_all_mails = lambda: None

    runner.add_post_run_hook(
        lambda: zip_and_mail_output_dir(
            output_dir=runner._resolved_excel_output_dir(),
            mail_settings=runner.settings['smtp_options'],
            recipient=args.recipient,
            subject='RSA',
            keep_archive=args.keep_archive,
        )
    )

    runner.run_selected([args.report])
    print(f'Klaar: report {args.report} uitgevoerd, output gezipt en gemaild naar {args.recipient}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


