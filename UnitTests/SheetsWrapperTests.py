import sys
from pathlib import Path

# Ensure project root is on sys.path so tests can import local packages like `outputs`
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest

from outputs.sheets_cell import SheetsCell
from outputs.sheets_wrapper import SheetsWrapper


def test_calculate_cell_range_no_cell_or_no_data():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
    with pytest.raises(ValueError):
        sheetsWrapper.calculate_cell_range_by_data(SheetsCell(''), [['']])
    with pytest.raises(ValueError):
        sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [])


def test_calculate_cell_range_A1_1_cell():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [['']])
    assert cell_range == 'A1:A1'


def test_calculate_cell_range_A1_2_cells_in_1_row():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [['', '']])
    assert cell_range == 'A1:B1'


def test_calculate_cell_range_A1_2_cells_in_1_column():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [[''], ['']])
    assert cell_range == 'A1:A2'


def test_number_of_nonempty_rows_in_data_empty_data():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([])
    assert number_of_rows == 0
    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([[]])
    assert number_of_rows == 0
    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['']])
    assert number_of_rows == 0


def test_number_of_nonempty_rows_in_data_1_row():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['']])
    assert number_of_rows == 1
    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a']])
    assert number_of_rows == 1


def test_number_of_nonempty_rows_in_data_2_rows():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['a'], ['']])
    assert number_of_rows == 2
    number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['a']])
    assert number_of_rows == 2


def test_get_range_dimensions_invalid_ranges():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
    with pytest.raises(ValueError):
        sheetsWrapper._get_range_dimensions('')
    with pytest.raises(ValueError):
        sheetsWrapper._get_range_dimensions('A:A:A')
    with pytest.raises(ValueError):
        sheetsWrapper._get_range_dimensions('A1:2')


def test_get_range_dimensions_valid_ranges():
    sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
    dims = sheetsWrapper._get_range_dimensions('A1:A1')
    assert dims[0] == 1
    assert dims[1] == 1

    dims = sheetsWrapper._get_range_dimensions('A1:C2')
    assert dims[0] == 2
    assert dims[1] == 3
