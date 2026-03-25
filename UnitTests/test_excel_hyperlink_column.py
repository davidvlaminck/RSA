from pathlib import Path
import sys

# ensure repo root on path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from outputs.excel import ExcelOutput
import openpyxl


def test_add_hyperlink_column_via_write_report(tmp_path):
    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    ex = ExcelOutput(output_dir=str(out_dir))

    wb_path = out_dir / 'test_hyperlink.xlsx'

    # create base workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Resultaat'
    wb.save(wb_path)

    # prepare QueryResult-like object
    from datasources.base import QueryResult
    keys = ['id', 'naam']
    rows = [['123', 'row1'], ['456', 'row2']]
    qr = QueryResult(keys=keys, rows=rows, last_data_update='2020-01-01')

    class Ctx:
        spreadsheet_id = str(wb_path)
        report_title = 'Test'
        datasource_name = 'ds'
        now_utc = '2020-01-01 00:00:00'
        excel_filename = wb_path.name

    ctx = Ctx()

    # call write_report which should add hyperlink column in column A data rows
    ex.write_report(ctx, qr, startcell='A1', add_filter=True, link_type='awvinfra')

    wb2 = openpyxl.load_workbook(wb_path)
    ws2 = wb2['Resultaat']

    # data rows begin at A4 (meta1/meta2/header then data start)
    assert ws2['A4'].hyperlink is not None
    assert 'awvinfra' in ws2['A4'].hyperlink.target
    assert ws2['A4'].value == '123'
    assert ws2['A5'].value == '456'

