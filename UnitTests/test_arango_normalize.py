import datetime
from datasources.arango import ArangoDatasource


class DummyConn:
    def __init__(self):
        self.aql = None


def test_normalize_last_data_update_datetime_naive_and_aware():
    conn = DummyConn()
    ds = ArangoDatasource.from_existing_connection(conn)

    # naive datetime -> treat as UTC and format
    naive = datetime.datetime(2026, 2, 13, 12, 30, 45)
    out = ds._normalize_last_data_update(naive)
    assert out == '2026-02-13 12:30:45'

    # aware datetime in CET (UTC+1)
    aware = datetime.datetime(2026, 2, 13, 13, 30, 45, tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
    out2 = ds._normalize_last_data_update(aware)
    assert out2 == '2026-02-13 12:30:45'


def test_normalize_last_data_update_iso_strings_and_formats():
    conn = DummyConn()
    ds = ArangoDatasource.from_existing_connection(conn)

    iso_with_offset = '2026-02-13T13:30:45+01:00'
    assert ds._normalize_last_data_update(iso_with_offset) == '2026-02-13 12:30:45'

    plain_format = '2026-02-13 13:30:45'
    assert ds._normalize_last_data_update(plain_format) == '2026-02-13 13:30:45'

    unknown = 'not a date'
    assert ds._normalize_last_data_update(unknown) is None

