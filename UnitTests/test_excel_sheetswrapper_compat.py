import openpyxl
from outputs.excel import ExcelOutput
from pathlib import Path


def test_get_sheets_and_read_data_and_find_first_nonempty(tmp_path):
    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    ex = ExcelOutput(output_dir=str(out_dir))

    wb_path = out_dir / 'testbook.xlsx'
    # create workbook and sheet with data
    ex.create_workbook_if_missing(wb_path)
    ex.create_sheet(wb_path, 'Resultaat', clear_if_exists=True)

    data = [
        ['meta1'],
        ['meta2'],
        ['uuid', 'naam'],
        ['a1', 'row1'],
        ['', ''],
        ['a3', 'row3']
    ]

    # write full data using write_data_to_sheet (it will overwrite/create)
    ex.write_data_to_sheet(wb_path, 'Resultaat', data, overwrite=True)

    # get sheets
    sheets = ex.get_sheets_in_spreadsheet(str(wb_path))
    assert 'Resultaat' in sheets
    props = sheets['Resultaat']['gridProperties']
    assert props['rowCount'] >= 6

    # read full sheet
    rows = ex.read_data_from_sheet(str(wb_path), 'Resultaat')
    assert len(rows) >= 6
    assert rows[2][0] == 'uuid'

    # find first non-empty in column A starting at A1 -> should be row 1 (meta)
    r1 = ex.find_first_nonempty_row_from_starting_cell(str(wb_path), 'Resultaat', 'A1')
    assert r1 == 1

    # find first non-empty in column A starting at A4 -> should be 4
    r4 = ex.find_first_nonempty_row_from_starting_cell(str(wb_path), 'Resultaat', 'A4')
    assert r4 == 4

    # read a range A4:B4
    rng = ex.read_data_from_sheet(str(wb_path), 'Resultaat', 'A4:B4')
    assert rng == [['a1', 'row1']]

