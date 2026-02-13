#!/usr/bin/env python3
"""Run a single report using real datasources (ArangoDB/PostGIS) and write Excel output.

This script is intended for local testing of a single report (default: Report0002).
It reads DB credentials from a settings JSON and initializes connectors.

Options:
  --settings PATH    Settings JSON (contains databases credentials)
  --report NAME      Report class name in Reports (default: Report0002)
  --skip-google      Don't call Google Sheets wrapper (stub minimal behavior)

Example:
  python3 scripts/run_report_real.py --settings /path/to/settings.json --report Report0002 --skip-google

"""
import argparse
import json
import logging
import sys
from pathlib import Path
from importlib import import_module
import os
import warnings

# Suppress known third-party DeprecationWarnings (narrow filter)
warnings.filterwarnings('ignore', message='path is deprecated. Use files\(\) instead', category=DeprecationWarning)

# Ensure project root is on sys.path so local imports work when running this script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Local imports (project)
from lib.reports.Report import Report

# We'll import connectors dynamically once we know settings


def load_settings(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")
    with open(p, 'r', encoding='utf-8') as fh:
        return json.load(fh)


class DummySheetsWrapper:
    def read_data_from_sheet(self, spreadsheet_id=None, sheet_name=None, sheetrange=None, return_raw_results=False, **kwargs):
        # When the caller requests raw results, return the structure; otherwise return a list of rows
        if return_raw_results:
            return {'values': [], 'range': f'{sheet_name}!A1:A1'}
        # Default: return empty list (no rows)
        return []

    def get_sheets_in_spreadsheet(self, spreadsheet_id):
        return {}

    def find_first_nonempty_row_from_starting_cell(self, *args, **kwargs):
        return 2

    def read_celldata_from_sheet(self, *args, **kwargs):
        return {'startRow': 4, 'rowData': []}

    def insert_empty_rows(self, *args, **kwargs):
        return None

    def write_data_to_sheet(self, *args, **kwargs):
        return None


class DummyMailSender:
    def add_sheet_info(self, *args, **kwargs):
        logging.debug('DummyMailSender.add_sheet_info called')

    def add_mail(self, *args, **kwargs):
        logging.info('DummyMailSender.add_mail suppressed')


def init_arango_from_settings(settings: dict):
    # find arango settings in several possible keys
    dbs = settings.get('databases', {})
    arango_conf = None
    for key in ('ArangoDB', 'arangodb', 'Arango', 'arango'):
        if key in dbs:
            arango_conf = dbs[key]
            break
    if not arango_conf:
        raise KeyError('ArangoDB settings not found in settings file under databases')

    host = arango_conf.get('host') or arango_conf.get('host', 'localhost')
    port = arango_conf.get('port') or arango_conf.get('http_port') or arango_conf.get('port', 8529)
    user = arango_conf.get('user') or arango_conf.get('username')
    password = arango_conf.get('password')
    database = arango_conf.get('database') or arango_conf.get('db')

    # Import and initialize SingleArangoConnector
    try:
        from datasources.arango import SingleArangoConnector
    except Exception as e:
        raise RuntimeError('Cannot import SingleArangoConnector: ' + str(e))

    logging.info('Initializing SingleArangoConnector with settings: %s:%s db=%s', host, port, database)
    SingleArangoConnector.init(host=str(host), port=str(port), user=user, password=password, database=database)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run a single report against real datasources and write Excel output')
    DEFAULT_SETTINGS_PATH = r'/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'
    parser.add_argument('--settings', default=DEFAULT_SETTINGS_PATH, help='Path to settings JSON (default: %(default)s)')
    parser.add_argument('--report', default='Report0002', help='Report class name in Reports package')
    parser.add_argument('--skip-google', action='store_true', help='Stub Google Sheets wrapper (avoid external API calls)')
    parser.add_argument('--workdir', default=str(PROJECT_ROOT), help='Working directory where RSA_OneDrive and files are located (default: project root)')

    # allow calling main() without explicitly passing --settings by injecting default
    if argv is None:
        argv = sys.argv[1:]
    # if the user didn't pass --settings or --settings=..., prepend default
    if not any(a == '--settings' or a.startswith('--settings=') for a in argv):
        argv = ['--settings', DEFAULT_SETTINGS_PATH] + argv
    args = parser.parse_args(argv)

    # change working directory to user-provided path so relative paths (RSA_OneDrive etc.) resolve correctly
    try:
        workdir = Path(args.workdir).expanduser().resolve()
        if not workdir.exists():
            raise FileNotFoundError(f'Workdir does not exist: {workdir}')
        os.chdir(str(workdir))
        logging.debug('Changed working directory to %s', workdir)
    except Exception as e:
        logging.error('Could not set working directory (%s): %s', args.workdir, e)
        return 5

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    settings = load_settings(args.settings)

    # Initialize ArangoDB connector if present
    try:
        init_arango_from_settings(settings)
    except Exception as e:
        logging.error('Arango init failed: %s', e)
        return 2

    # Initialize PostGIS connector (if configured)
    try:
        postgis_conf = settings.get('databases', {}).get('PostGIS') or settings.get('databases', {}).get('postgis')
        if postgis_conf:
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            SinglePostGISConnector.init(host=postgis_conf.get('host'), port=str(postgis_conf.get('port')),
                                        user=postgis_conf.get('user'), password=postgis_conf.get('password'),
                                        database=postgis_conf.get('database'))
            logging.info('Initialized SinglePostGISConnector')
    except Exception as e:
        logging.warning('Could not initialize PostGIS connector: %s', e)

    # Initialize Excel writer (best-effort)
    try:
        out_dir = settings.get('output', {}).get('excel', {}).get('output_dir', None)
        if out_dir is None:
            out_dir = str(Path.cwd() / 'RSA_OneDrive')
        from outputs.excel_wrapper import SingleExcelWriter
        SingleExcelWriter.init(output_dir=out_dir)
        logging.info('Initialized SingleExcelWriter with dir: %s', out_dir)
    except Exception as e:
        logging.warning('Could not initialize SingleExcelWriter: %s', e)

    # Optionally stub Google Sheets wrapper to avoid API calls
    if args.skip_google:
        try:
            mod = import_module('outputs.sheets_wrapper')
            if hasattr(mod, 'SingleSheetsWrapper'):
                mod.SingleSheetsWrapper.get_wrapper = staticmethod(lambda: DummySheetsWrapper())
                logging.info('Patched SingleSheetsWrapper.get_wrapper to DummySheetsWrapper')
        except Exception:
            logging.debug('Could not patch SheetsWrapper (module not found)')

    # Always ensure SingleSheetsWrapper.get_wrapper will not raise RuntimeError when not initialized.
    # This makes the test runner robust: if the wrapper wasn't initialized (no Google creds),
    # the DQReport code will still be able to run using DummySheetsWrapper.
    try:
        mod = import_module('outputs.sheets_wrapper')
        if hasattr(mod, 'SingleSheetsWrapper'):
            orig_get = mod.SingleSheetsWrapper.get_wrapper

            def safe_get_wrapper():
                try:
                    return orig_get()
                except RuntimeError:
                    return DummySheetsWrapper()

            mod.SingleSheetsWrapper.get_wrapper = staticmethod(safe_get_wrapper)
            logging.debug('Installed safe SingleSheetsWrapper.get_wrapper fallback')
    except Exception:
        logging.debug('Could not install safe wrapper fallback (module missing)')

    # Import report class dynamically
    try:
        rpt_mod = import_module(f'Reports.{args.report}')
    except Exception as e:
        logging.error('Cannot import report module Reports.%s: %s', args.report, e)
        return 3

    try:
        # instantiate and init
        rpt_cls = getattr(rpt_mod, args.report)
        rpt_inst: Report = rpt_cls()
        if hasattr(rpt_inst, 'init_report'):
            rpt_inst.init_report()
        else:
            logging.warning('Report %s has no init_report method', args.report)

        # run report with dummy mail sender to avoid sending emails
        sender = DummyMailSender()
        logging.info('Running report %s ...', args.report)
        # Determine expected output path before running so we can check if it changed
        try:
            expected_excel = getattr(rpt_inst.report, 'excel_filename', None)
        except Exception:
            expected_excel = None
        if expected_excel:
            out_path = Path('RSA_OneDrive') / expected_excel
        else:
            out_path = Path('RSA_OneDrive') / (rpt_inst.report.title.replace('/', '_') + '.xlsx')

        pre_mtime = None
        if out_path.exists():
            try:
                pre_mtime = out_path.stat().st_mtime
            except Exception:
                pre_mtime = None

        rpt_inst.run_report(sender=sender)
        logging.info('Report run finished')

        # Small safety window: some environments may have a tiny delay between write completion
        # and filesystem visibility (esp. when fallback wrote in-memory and OS syncs). Poll briefly
        # before emitting a warning to avoid false negatives.
        import time
        found = False
        for _ in range(50):  # poll for up to ~10 seconds (50 * 0.2s)
            if out_path.exists():
                found = True
                break
            time.sleep(0.2)

        if found:
            # Check whether file was modified since we started
            try:
                post_mtime = out_path.stat().st_mtime
            except Exception:
                post_mtime = None

            if pre_mtime is None:
                logging.info('Report output written to: %s (new file)', out_path)
            elif post_mtime is not None and post_mtime > pre_mtime:
                logging.info('Report output written to: %s (updated)', out_path)
            else:
                logging.warning('Report output file exists but was NOT modified by this run: %s (mtime unchanged)', out_path)
                # show backups if present
                backups = list(Path('RSA_OneDrive').glob(out_path.stem + '_backup_*' + out_path.suffix))
                if backups:
                    logging.info('Backups found for this file: %s', backups)
        else:
            logging.warning('Expected output file not found after waiting: %s', out_path)

        return 0
    except Exception as e:
        logging.exception('Report execution failed: %s', e)
        return 4


if __name__ == '__main__':
    raise SystemExit(main())

