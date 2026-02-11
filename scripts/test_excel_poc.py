from outputs.excel import ExcelOutput
from outputs.base import OutputWriteContext
from pathlib import Path
import traceback

try:
    w = ExcelOutput(output_dir='RSA_OneDrive')
    ctx = OutputWriteContext(spreadsheet_id='x', report_title='Test Report', datasource_name='ArangoDB', now_utc='now', excel_filename='test_poc.xlsx')

    class DummyQR:
        def __init__(self):
            self.keys = ['a.uuid', 'a.naam']
            self.rows = [['628edbc5-5c33-4365-8fcf-2970e326f3e4','tlc-fi-broker'], ['8c01c72a-fb19-4a3a-8d4f-d22574868517','tlc-fi-broker']]
            self.last_data_update = '2026-02-11T00:00:00+00:00'
        def iter_rows(self):
            for r in self.rows:
                yield r
        @property
        def query_time_seconds(self):
            return 0.123

    qr = DummyQR()
    meta = w.write_report(ctx, qr)
    print('meta ->', meta)
    # read back
    rows = list(w.iter_rows(Path('RSA_OneDrive') / 'test_poc.xlsx', 'Resultaat'))
    print('rows read back:')
    for r in rows:
        print(r)
except Exception:
    traceback.print_exc()
    raise
