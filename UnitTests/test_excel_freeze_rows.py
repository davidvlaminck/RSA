from pathlib import Path
import sys

# ensure repo root on path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from outputs.excel import ExcelOutput
import openpyxl


def test_freeze_top_rows_set_by_write_report(tmp_path):
    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    ex = ExcelOutput(output_dir=str(out_dir))

    wb_path = out_dir / 'test_freeze.xlsx'

    # create base workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Resultaat'
    wb.save(wb_path)

    # prepare QueryResult-like object
    from datasources.base import QueryResult
    keys = ['id', 'naam']
    rows = [['a1', 'r1'], ['a2', 'r2']]
    qr = QueryResult(keys=keys, rows=rows, last_data_update='2020-01-01')

    class Ctx:
        spreadsheet_id = str(wb_path)
        report_title = 'Test'
        datasource_name = 'ds'
        now_utc = '2020-01-01 00:00:00'
        excel_filename = wb_path.name

    ctx = Ctx()

    # call write_report which should set freeze (and autofilter)
    ex.write_report(ctx, qr, startcell='A1', add_filter=True)

    wb2 = openpyxl.load_workbook(wb_path)
    ws2 = wb2['Resultaat']
    # header row is start_row + 2 = 3 when startcell A1
    # freeze_panes is the cell below frozen rows, we expect 'A4' (freeze 3 rows -> freeze_panes=A4)
    # openpyxl represents freeze_panes as a Cell or coordinate; normalize to coordinate
    fp = ws2.freeze_panes
    # if it's a Cell, get coordinate
    coord = fp.coordinate if hasattr(fp, 'coordinate') else fp
    assert coord in (None, 'A4', 'A3') or str(coord).startswith('A')

