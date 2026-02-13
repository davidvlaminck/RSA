import os
import json
from pathlib import Path
from importlib import import_module

from outputs.excel_wrapper import SingleExcelWriter


class DummyMailSender:
    def add_sheet_info(self, *a, **k): pass
    def add_mail(self, *a, **k): pass


class DummySheetsWrapper:
    def read_data_from_sheet(self, *args, **kwargs):
        # mimic SheetsWrapper: when return_raw_results=True, return a dict with 'values' and 'range'
        if kwargs.get('return_raw_results', False):
            return {'values': [], 'range': 'Overzicht!A1:A1'}
        return []

    def get_sheets_in_spreadsheet(self, *args, **kwargs):
        return {}

    def find_first_nonempty_row_from_starting_cell(self, *args, **kwargs):
        return 4

    def read_celldata_from_sheet(self, *args, **kwargs):
        return {'startRow': 4, 'rowData': []}

    def insert_empty_rows(self, *args, **kwargs):
        return None

    def write_data_to_sheet(self, *args, **kwargs):
        return None

    def get_sheets_in_spreadsheet(self, *args, **kwargs):
        return {'Resultaat': {'gridProperties': {'rowCount': 1000}}}


def run_report_to_dir(report_name: str, out_dir: Path):
    # initialize singleton
    SingleExcelWriter.init(output_dir=str(out_dir))

    # install dummy sheets wrapper to avoid Google calls during tests
    try:
        from outputs.sheets_wrapper import SingleSheetsWrapper
        SingleSheetsWrapper.sheets_wrapper = DummySheetsWrapper()
    except Exception:
        pass

    # import and instantiate report
    mod = import_module(f'Reports.{report_name}')
    cls = getattr(mod, report_name)
    rpt = cls()
    if hasattr(rpt, 'init_report'):
        rpt.init_report()
    # run
    rpt.run_report(sender=DummyMailSender())

    # check file
    fname = rpt.report.excel_filename
    target = out_dir / fname
    assert target.exists(), f'Expected file {target} to exist'
    # quick header check via openpyxl
    import openpyxl
    wb = openpyxl.load_workbook(target, read_only=True)
    ws = wb['Resultaat']
    rows = list(ws.iter_rows(values_only=True))
    assert len(rows) >= 3
    header = rows[2]
    assert header[0] is not None


def test_report0002_and_0030(tmp_path):
    # integration tests require a real ArangoDB connection. Try to load settings and initialize the connector.
    settings_path = os.environ.get('RSA_SETTINGS') or '/home/davidlinux/Documenten/AWV/resources/settings_RSA.json'
    if not Path(settings_path).exists():
        import pytest
        pytest.skip(f'ArangoDB settings not found at {settings_path}; skipping integration test')

    # initialize SingleArangoConnector from settings
    with open(settings_path, 'r', encoding='utf-8') as fh:
        settings = json.load(fh)
    arango_conf = settings.get('databases', {}).get('ArangoDB') or settings.get('databases', {}).get('arangodb')
    if not arango_conf:
        import pytest
        pytest.skip('No ArangoDB config in settings; skipping')

    from datasources.arango import SingleArangoConnector
    SingleArangoConnector.init(host=arango_conf.get('host'), port=str(arango_conf.get('port')), user=arango_conf.get('user'), password=arango_conf.get('password'), database=arango_conf.get('database'))

    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    run_report_to_dir('Report0002', out_dir)
    run_report_to_dir('Report0030', out_dir)
