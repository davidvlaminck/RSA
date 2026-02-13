import tempfile
from pathlib import Path
import pytest
from outputs.excel import ExcelOutput
from outputs.base import OutputWriteContext

class DummyQR:
    def __init__(self, rows, keys=None, last_data_update=None):
        self.rows = rows
        self._keys = keys or (['c1','c2'] if rows else [])
        self.last_data_update = last_data_update
    @property
    def keys(self):
        return self._keys
    def iter_rows(self):
        for r in self.rows:
            yield r


def test_create_and_write_small(tmp_path):
    out_dir = tmp_path / 'out'
    writer = ExcelOutput(output_dir=str(out_dir))
    rows = [['a','1'], ['b','2']]
    qr = DummyQR(rows, keys=['uuid','naam'], last_data_update='2026-02-11T00:00:00')
    ctx = OutputWriteContext(spreadsheet_id='x', report_title='t', datasource_name='ArangoDB', now_utc='now', excel_filename='small_test.xlsx')
    meta = writer.write_report(ctx, qr)
    assert meta is not None
    f = out_dir / 'small_test.xlsx'
    assert f.exists()


def test_write_streaming_large(tmp_path):
    out_dir = tmp_path / 'out'
    writer = ExcelOutput(output_dir=str(out_dir))
    # generate many rows lazily
    def gen():
        for i in range(2000):
            yield [f'id_{i}', str(i)]
    qr = DummyQR(None, keys=['uuid','val'], last_data_update='2026-02-11')
    # monkeypatch iter_rows to use generator
    qr.iter_rows = gen
    ctx = OutputWriteContext(spreadsheet_id='x', report_title='t', datasource_name='ArangoDB', now_utc='now', excel_filename='big_test.xlsx')
    meta = writer.write_report(ctx, qr)
    assert meta is not None
    assert meta['rows_written'] >= 2000
    f = out_dir / 'big_test.xlsx'
    assert f.exists()

