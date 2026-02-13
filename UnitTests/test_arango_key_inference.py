import pytest
from datasources.arango import ArangoDatasource
from datasources.base import QueryResult


class FakeCursorNoKeys:
    def __init__(self, rows):
        # rows: list of dicts or lists
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)


class FakeCursorWithKeys:
    def __init__(self, rows, keys):
        self._rows = rows
        self._keys = keys

    def __iter__(self):
        return iter(self._rows)

    def keys(self):
        return list(self._keys)


class FakeAQL:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query):
        return self._cursor


class FakeConnection:
    def __init__(self, cursor):
        self.aql = FakeAQL(cursor)


def test_infer_keys_from_dict_rows_preserve_order():
    # First row has keys b, a (in that order), second row adds c
    rows = [
        {"b": 1, "a": 2},
        {"c": 3, "a": 4},
    ]
    cursor = FakeCursorNoKeys(rows)
    conn = FakeConnection(cursor)
    ds = ArangoDatasource.from_existing_connection(conn)

    qr = ds.execute("RETURN 1")

    assert isinstance(qr, QueryResult)
    # Expect keys in first-seen order: b, a, c
    assert qr.keys == ["b", "a", "c"]


def test_use_cursor_keys_if_present_overrides_row_inference():
    rows = [
        {"x": 1, "y": 2},
        {"y": 3, "z": 4},
    ]
    cursor = FakeCursorWithKeys(rows, keys=["col1", "col2"])  # artificial keys
    conn = FakeConnection(cursor)
    ds = ArangoDatasource.from_existing_connection(conn)

    qr = ds.execute("RETURN 1")
    assert qr.keys == ["col1", "col2"]


def test_no_keys_for_non_dict_rows():
    rows = [
        (1, "a"),
        (2, "b"),
    ]
    cursor = FakeCursorNoKeys(rows)
    conn = FakeConnection(cursor)
    ds = ArangoDatasource.from_existing_connection(conn)

    qr = ds.execute("RETURN 1")
    assert qr.keys == []

