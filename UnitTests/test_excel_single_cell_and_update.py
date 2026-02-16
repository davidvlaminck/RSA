from outputs.excel import ExcelOutput
from pathlib import Path


def test_write_single_cell_and_update(tmp_path):
    out_dir = tmp_path / 'rsa_out'
    out_dir.mkdir()
    ex = ExcelOutput(output_dir=str(out_dir))

    wb_path = out_dir / 'singlecell.xlsx'
    ex.create_workbook_if_missing(wb_path)
    ex.create_sheet(wb_path, 'Resultaat', clear_if_exists=True)

    # write single cell A1
    ex.write_single_cell(str(wb_path), 'Resultaat', 'A1', 'hello')

    rows = ex.read_data_from_sheet(str(wb_path), 'Resultaat')
    assert rows[0][0] == 'hello'

    # update a numeric counter at B1
    ex.write_single_cell(str(wb_path), 'Resultaat', 'B1', 1)
    ex.update_row_by_adding_number(str(wb_path), 'Resultaat', 'B1', 2)
    rows2 = ex.read_data_from_sheet(str(wb_path), 'Resultaat')
    assert rows2[0][1] == 3

