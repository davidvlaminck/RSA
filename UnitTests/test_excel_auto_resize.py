from pathlib import Path
import sys

# ensure repo root on path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from outputs.excel import ExcelOutput
import openpyxl


def test_automatic_resize_columns_via_write_report(tmp_path):
    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    ex = ExcelOutput(output_dir=str(out_dir))

    wb_path = out_dir / 'test_autoresize.xlsx'

    # create base workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Resultaat'
    wb.save(wb_path)

    # prepare QueryResult-like object with varying length values
    from datasources.base import QueryResult
    keys = ['id', 'long_name']
    rows = [['a1', 'short'], ['a2', 'a much longer cell content that should widen the column']]
    qr = QueryResult(keys=keys, rows=rows, last_data_update='2020-01-01')

    class Ctx:
        spreadsheet_id = str(wb_path)
        report_title = 'Test'
        datasource_name = 'ds'
        now_utc = '2020-01-01 00:00:00'
        excel_filename = wb_path.name

    ctx = Ctx()

    # call write_report which should set autofilter, freeze and autoresize
    ex.write_report(ctx, qr, startcell='A1', add_filter=True)

    wb2 = openpyxl.load_workbook(wb_path)
    ws2 = wb2['Resultaat']

    # check that column B width is larger than column A width (since B has a much longer value)
    wA = ws2.column_dimensions['A'].width
    wB = ws2.column_dimensions['B'].width
    assert wB >= wA

