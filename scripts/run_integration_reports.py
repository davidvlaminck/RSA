#!/usr/bin/env python3
"""Run multiple reports against real datasources and write Excel outputs.

Usage:
  python3 scripts/run_integration_reports.py --settings /path/to/settings.json --reports Report0002 Report0030 --outdir /tmp/rsa_out

The script will:
- initialize DB connectors (Arango, PostGIS, Neo4j) from settings
- initialize SingleExcelWriter pointing to --outdir (default: tmpdir)
- run each report: import, init_report(), run_report(sender=DummyMailSender())
- collect per-report status and print a summary

If settings file is not found, the script will exit with an explanatory message.
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from importlib import import_module
from pathlib import Path

# ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.reports.Report import Report


class DummySheetsWrapper:
    def read_data_from_sheet(self, *args, **kwargs):
        return []

    def get_sheets_in_spreadsheet(self, *args, **kwargs):
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


def load_settings(p: str) -> dict:
    path = Path(p)
    if not path.exists():
        raise FileNotFoundError(f'Settings file not found: {p}')
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def init_connectors(settings: dict):
    # Arango
    try:
        arango_conf = settings.get('databases', {}).get('ArangoDB') or settings.get('databases', {}).get('arangodb')
        if arango_conf:
            from datasources.arango import SingleArangoConnector
            SingleArangoConnector.init(host=arango_conf.get('host'), port=str(arango_conf.get('port')),
                                       user=arango_conf.get('user'), password=arango_conf.get('password'),
                                       database=arango_conf.get('database'))
            logging.info('Initialized SingleArangoConnector')
    except Exception as e:
        logging.warning('Arango init failed: %s', e)

    # PostGIS
    try:
        postgis_conf = settings.get('databases', {}).get('PostGIS') or settings.get('databases', {}).get('postgis')
        if postgis_conf:
            from lib.connectors.PostGISConnector import SinglePostGISConnector
            SinglePostGISConnector.init(host=postgis_conf.get('host'), port=str(postgis_conf.get('port')),
                                        user=postgis_conf.get('user'), password=postgis_conf.get('password'),
                                        database=postgis_conf.get('database'))
            logging.info('Initialized SinglePostGISConnector')
    except Exception as e:
        logging.warning('PostGIS init failed: %s', e)

    # Neo4j
    try:
        neo4j_conf = settings.get('databases', {}).get('Neo4j')
        if neo4j_conf:
            from lib.connectors.Neo4JConnector import SingleNeo4JConnector
            SingleNeo4JConnector.init(uri=neo4j_conf.get('uri'), user=neo4j_conf.get('user'),
                                      password=neo4j_conf.get('password'), database=neo4j_conf.get('database'))
            logging.info('Initialized SingleNeo4JConnector')
    except Exception as e:
        logging.warning('Neo4J init failed: %s', e)


def safe_sheets_wrapper(settings: dict):
    # Patch SingleSheetsWrapper.get_wrapper to return Dummy when not initialized
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
            logging.debug('Patched SingleSheetsWrapper.get_wrapper to safe variant')
    except Exception:
        logging.debug('Could not patch SheetsWrapper')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', required=True)
    parser.add_argument('--reports', nargs='+', required=True)
    parser.add_argument('--outdir', default=None)
    args = parser.parse_args(argv)

    settings = load_settings(args.settings)

    # init connectors
    init_connectors(settings)

    # prepare outdir
    if args.outdir:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
    else:
        tmp = tempfile.TemporaryDirectory(prefix='rsa_integration_')
        outdir = Path(tmp.name)

    # init excel writer
    try:
        from outputs.excel_wrapper import SingleExcelWriter
        SingleExcelWriter.init(output_dir=str(outdir))
    except Exception as e:
        logging.warning('Could not init SingleExcelWriter: %s', e)

    # make sheets wrapper safe
    safe_sheets_wrapper(settings)

    summary = {}
    failed = []
    for rpt in args.reports:
        logging.info('Running report %s', rpt)
        try:
            mod = import_module(f'Reports.{rpt}')
            cls = getattr(mod, rpt)
            inst = cls()
            if hasattr(inst, 'init_report'):
                inst.init_report()
            inst.run_report(sender=DummyMailSender())
            summary[rpt] = 'ok'
            logging.info('✓ %s done', rpt)
        except Exception as e:
            logging.exception('Report %s failed: %s', rpt, e)
            summary[rpt] = f'failed: {e}'
            failed.append(rpt)

    print('\nIntegration run summary:')
    for k, v in summary.items():
        print(f' - {k}: {v}')

    if failed:
        return 2
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())

