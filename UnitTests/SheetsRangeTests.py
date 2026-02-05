import sys
from pathlib import Path

# Ensure project root is on sys.path so tests can import local modules like `outputs`
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest

from outputs.sheets_cell import SheetsCell


def test_init_SheetsRange():
    range1 = SheetsCell('A1')
    assert range1.cell == 'A1'
    assert range1._column_str == 'A'
    assert range1._column_int == 1
    assert range1._row == 1


def test_update_SheetsRange():
    range1 = SheetsCell('A1')
    range1.update_row_by_adding_number(1)
    assert range1.cell == 'A2'
    range1.update_column_by_adding_number(1)
    assert range1.cell == 'B2'


def test_create_second_SheetsRange():
    range1 = SheetsCell('A1')
    range2 = range1.copy()
    range2.cell = 'B2'
    assert range2.cell == 'B2'
    assert range1.cell == 'A1'


def test_convert_number_to_column():
    testlist = [(1, 'A'),
                (2, 'B'),
                (26, 'Z'),
                (27, 'AA'),
                (28, 'AB'),
                (53, 'BA'),
                (702, 'ZZ'),
                (703, 'AAA'),
                (729, 'ABA'),
                (18278, 'ZZZ')]

    for num, expected in testlist:
        column = SheetsCell._convert_number_to_column(num)
        assert column == expected

    # invalid values
    with pytest.raises(ValueError):
        SheetsCell._convert_number_to_column(18279)
    with pytest.raises(ValueError):
        SheetsCell._convert_number_to_column(0)


def test_convert_column_to_number():
    testlist = [(1, 'A'),
                (2, 'B'),
                (26, 'Z'),
                (27, 'AA'),
                (28, 'AB'),
                (53, 'BA'),
                (702, 'ZZ'),
                (703, 'AAA'),
                (729, 'ABA'),
                (18278, 'ZZZ')]

    for expected, col in testlist:
        number = SheetsCell._convert_column_to_number(col)
        assert number == expected

    with pytest.raises(ValueError):
        SheetsCell._convert_column_to_number('')
    with pytest.raises(ValueError):
        SheetsCell._convert_column_to_number('AAAA')
