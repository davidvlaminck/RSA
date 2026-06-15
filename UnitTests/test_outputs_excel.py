import pytest
from typing import Any, cast
from outputs.excel import ExcelOutput, ExcelWriterError
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
    meta = cast(Any, writer).write_report(ctx, qr)
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
    meta = cast(Any, writer).write_report(ctx, qr)
    assert meta is not None
    assert meta['rows_written'] >= 2000  # type: ignore[index]
    f = out_dir / 'big_test.xlsx'
    assert f.exists()


def test_resolve_prefers_valid_bucket_workbook_over_corrupt_root(tmp_path):
    out_dir = tmp_path / 'out'
    writer = ExcelOutput(output_dir=str(out_dir))

    root = out_dir / 'sample.xlsx'
    bucket = out_dir / '0000-0099' / 'sample.xlsx'
    bucket.parent.mkdir(parents=True, exist_ok=True)

    # corrupt root workbook: looks like an xlsx file but is not a valid zip archive
    root.write_text('not a real xlsx', encoding='utf-8')

    # create a valid bucket workbook directly
    writer.write_data_to_sheet(bucket, 'Overzicht', [['header'], ['value']], overwrite=True)

    resolved = writer._resolve_workbook_path('sample.xlsx')
    assert resolved == bucket
    assert resolved.exists()


def test_reject_root_level_workbook_write_in_onedrive(tmp_path):
    out_dir = tmp_path / 'RSA_OneDrive'
    writer = ExcelOutput(output_dir=str(out_dir))

    with pytest.raises(ExcelWriterError):
        writer.write_data_to_sheet(out_dir / 'root.xlsx', 'Overzicht', [['header'], ['value']], overwrite=True)


def test_missing_report_workbook_raises_clear_error(tmp_path):
    out_dir = tmp_path / 'RSA_OneDrive'
    writer = ExcelOutput(output_dir=str(out_dir))
    qr = DummyQR([['a', '1']], keys=['uuid', 'naam'], last_data_update='2026-02-11T00:00:00')
    ctx = OutputWriteContext(
        spreadsheet_id='x',
        report_title='Laagspanningsbord heeft minstens 1 Elektrische Keuring',
        datasource_name='ArangoDB',
        now_utc='now',
        report_name='report0223',
        excel_filename='[RSA] Laagspanningsbord heeft minstens 1 Elektrische Keuring.xlsx',
        report_number=223,
        require_existing_workbook=True,
    )

    with pytest.raises(ExcelWriterError) as excinfo:
        cast(Any, writer).write_report(ctx, qr)

    message = str(excinfo.value)
    assert 'report0223' in message
    assert '[RSA] Laagspanningsbord heeft minstens 1 Elektrische Keuring.xlsx' in message
    assert '0200-0299' in message


def test_overview_variant_fallback_repairs_canonical_summary(tmp_path):
    out_dir = tmp_path / 'RSA_OneDrive'
    writer = ExcelOutput(output_dir=str(out_dir))
    overview_dir = out_dir / 'Overzicht'
    overview_dir.mkdir(parents=True)

    alternate = overview_dir / '[RSA] Overzicht rapporten (3).xlsx'
    writer.write_data_to_sheet(alternate, 'Overzicht', [['header'], ['alternate']], overwrite=True)

    canonical = overview_dir / '[RSA] Overzicht rapporten.xlsx'
    canonical.write_text('not a real xlsx', encoding='utf-8')

    assert writer.read_data_from_sheet(canonical, 'Overzicht') == [['header'], ['alternate']]
    writer.write_single_cell(canonical, 'Overzicht', 'A1', 'fixed')
    assert writer.read_data_from_sheet(canonical, 'Overzicht') == [['fixed'], ['alternate']]


def test_invalid_overview_without_variant_is_recreated_for_writes(tmp_path):
    out_dir = tmp_path / 'RSA_OneDrive'
    writer = ExcelOutput(output_dir=str(out_dir))
    canonical = out_dir / 'Overzicht' / '[RSA] Overzicht rapporten.xlsx'
    canonical.parent.mkdir(parents=True)
    canonical.write_text('not a real xlsx', encoding='utf-8')

    writer.write_single_cell(canonical, 'Overzicht', 'A1', 'fixed')

    assert writer.read_data_from_sheet(canonical, 'Overzicht') == [['fixed']]

