from datetime import date
from unittest.mock import Mock

from lib.reports.DQReport import DQReport

bv_data = [('6e9c0d4f-73a9-4461-a01b-81436e26f112', '001A3', True, 'in-gebruik', 4.374456577708933, 51.124556377992405,
            'Aartselaar', 'Antwerpen', '1984-07-06', '1984-07-06', 'TV014026v01', 'TV01402', '', 'MDN/1504', 'YUNEX',
            False, False, '001A3/001A3.VR')]


def test_clean_empty():
    dqr = DQReport(Mock())

    result_empty_rows = dqr.clean([[], ['a']])
    assert result_empty_rows == [['a']]

    result_empty_rows = dqr.clean([(), tuple('a')])
    assert result_empty_rows == [['a']]


def test_clean_str_only():
    dqr = DQReport(Mock())
    multiple_str_elements = dqr.clean([['a', 'b']])
    assert multiple_str_elements == [['a', 'b']]


def test_clean_non_str_only():
    dqr = DQReport(Mock())
    multiple_int_elements = dqr.clean([[date(2021, 1, 1), 2.0]])
    assert multiple_int_elements == [['2021-01-01', '2.0']]


def test_clean_non_str_only_2():
    dqr = DQReport(Mock())
    multiple_int_elements = dqr.clean([['some str', True]])
    assert multiple_int_elements == [['some str', 'True']]

def test_clean_list():
    dqr = DQReport(Mock())
    multiple_int_elements = dqr.clean([[['some str', True]]])
    assert multiple_int_elements == [['some str|True']]
