"""
Unit tests for outputs/google_sheets.py helpers and GoogleSheetsWriter.build_table
"""

from datasources.base import QueryResult
from outputs.google_sheets import _json_safe_value, _json_safe_table, GoogleSheetsWriter
from decimal import Decimal
from datetime import datetime


def test_json_safe_value_basic_types():
    assert _json_safe_value(None) is None
    assert _json_safe_value(123) == 123
    assert _json_safe_value(12.3) == 12.3
    assert _json_safe_value('abc') == 'abc'
    assert _json_safe_value(True) is True


def test_json_safe_value_decimal_and_object():
    assert _json_safe_value(Decimal('12.34')) == '12.34'
    class X:
        def __str__(self):
            return 'X-STR'
    assert _json_safe_value(X()) == 'X-STR'


def test_json_safe_table():
    table = [[1, Decimal('1.23')], [None, 'a']]
    out = _json_safe_table(table)
    assert out[0][0] == 1
    assert out[0][1] == '1.23'
    assert out[1][0] is None


def test_build_table_from_queryresult_dict_rows():
    rows = [
        {'uuid': 'u1', 'naam': 'n1'},
        {'uuid': 'u2', 'naam': 'n2'},
    ]
    qr = QueryResult(keys=['uuid', 'naam'], rows=rows)
    gw = GoogleSheetsWriter(sheets_wrapper=object())
    table = gw.build_table(qr)
    assert table[0] == ['uuid', 'naam']
    assert table[1] == ['u1', 'n1']
    assert table[2] == ['u2', 'n2']


def test_build_table_with_persistent_column():
    rows = [
        {'uuid': 'u1', 'naam': 'n1'},
    ]
    qr = QueryResult(keys=['uuid', 'naam'], rows=rows)
    persistent = {'u1': 'keepme'}
    gw = GoogleSheetsWriter(sheets_wrapper=object())
    table = gw.build_table(qr, persistent_column='opm', persistent_dict=persistent)
    assert table[0][-1] == 'opmerkingen (blijvend)'
    assert table[1][-1] == 'keepme'
