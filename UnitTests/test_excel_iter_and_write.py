import os
import tempfile
import decimal
import datetime
from outputs.excel import ExcelOutput


def test_iter_rows_normalization():
    ex = ExcelOutput(output_dir=tempfile.gettempdir())

    headers = ["a", "b"]
    rows = ([decimal.Decimal('1.5'), datetime.date(2026, 2, 14)], [None, "x"])  # sequence

    it = ex.iter_rows(headers, rows)
    out = list(it)
    assert out[0] == headers
    # first data row: decimal -> float, date -> iso
    assert isinstance(out[1][0], float)
    assert out[1][1] == datetime.date(2026, 2, 14).isoformat()
    # second row: None -> ''
    assert out[2][0] == ''
    assert out[2][1] == 'x'


def test_write_data_streaming_and_readback():
    # Use a temporary directory and filename
    with tempfile.TemporaryDirectory() as td:
        ex = ExcelOutput(output_dir=td)
        fname = os.path.join(td, 'test_stream.xlsx')

        headers = ['id', 'name']

        def gen_rows():
            yield headers
            for i in range(3):
                yield [str(i), f'name-{i}']

        meta = ex.write_data_to_sheet(fname, 'Resultaat', gen_rows(), overwrite=True)
        assert meta['rows_written'] == 4  # header + 3 rows

        # read back
        data = ex.read_data_from_sheet(fname, 'Resultaat')
        assert data[0] == headers
        assert data[1] == ['0', 'name-0']
        assert data[3] == ['2', 'name-2']

