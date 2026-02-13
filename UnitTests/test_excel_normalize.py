import datetime
import decimal
from outputs.excel import ExcelOutput


def test_normalize_decimal_and_datetime():
    ex = ExcelOutput(output_dir='/tmp')

    d = decimal.Decimal('12.34')
    assert isinstance(ex._normalize_value(d), float)

    dt = datetime.datetime(2026, 2, 13, 15, 0, 0)
    # Should return isoformat
    assert ex._normalize_value(dt) == dt.isoformat()

    datev = datetime.date(2026, 2, 13)
    assert ex._normalize_value(datev) == datev.isoformat()

    assert ex._normalize_value(None) == ''
    assert ex._normalize_value('abc') == 'abc'

