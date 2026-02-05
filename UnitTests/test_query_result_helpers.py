"""
Unit tests for QueryResult helper methods.
Demonstrates datasource-independent data handling.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from datasources.base import QueryResult


def test_to_rows_list_with_dicts():
    """Test conversion of dict rows to list[list]."""
    result = QueryResult(
        keys=['id', 'name', 'value'],
        rows=[
            {'id': 1, 'name': 'Alice', 'value': 100},
            {'id': 2, 'name': 'Bob', 'value': 200},
        ],
        query_time_seconds=0.1,
    )

    rows_list = result.to_rows_list()

    assert rows_list == [
        [1, 'Alice', 100],
        [2, 'Bob', 200],
    ]


def test_to_rows_list_with_tuples():
    """Test conversion of tuple rows to list[list]."""
    result = QueryResult(
        keys=['id', 'name', 'value'],
        rows=[
            (1, 'Alice', 100),
            (2, 'Bob', 200),
        ],
        query_time_seconds=0.1,
    )

    rows_list = result.to_rows_list()

    assert rows_list == [
        [1, 'Alice', 100],
        [2, 'Bob', 200],
    ]


def test_to_rows_list_with_missing_dict_keys():
    """Test that missing keys in dicts return None."""
    result = QueryResult(
        keys=['id', 'name', 'value'],
        rows=[
            {'id': 1, 'name': 'Alice'},  # missing 'value'
            {'id': 2, 'value': 200},     # missing 'name'
        ],
        query_time_seconds=0.1,
    )

    rows_list = result.to_rows_list()

    assert rows_list == [
        [1, 'Alice', None],
        [2, None, 200],
    ]


def test_iter_rows_with_dicts():
    """Test streaming iteration over dict rows without loading all into memory."""
    result = QueryResult(
        keys=['id', 'name'],
        rows=[
            {'id': i, 'name': f'User{i}'}
            for i in range(1000)
        ],
        query_time_seconds=0.5,
    )

    row_count = 0
    for row in result.iter_rows():
        assert len(row) == 2
        assert isinstance(row[0], int)
        assert isinstance(row[1], str)
        row_count += 1

    assert row_count == 1000


def test_iter_rows_with_tuples():
    """Test streaming iteration over tuple rows."""
    result = QueryResult(
        keys=['id', 'name'],
        rows=[
            (i, f'User{i}')
            for i in range(1000)
        ],
        query_time_seconds=0.5,
    )

    row_count = 0
    for row in result.iter_rows():
        assert len(row) == 2
        row_count += 1

    assert row_count == 1000


def test_empty_result():
    """Test handling of empty resultsets."""
    result = QueryResult(
        keys=['id', 'name'],
        rows=[],
        query_time_seconds=0.01,
    )

    assert result.to_rows_list() == []
    assert list(result.iter_rows()) == []


def test_mixed_types_preservation():
    """Test that various types are preserved correctly."""
    result = QueryResult(
        keys=['id', 'amount', 'created', 'active'],
        rows=[
            {
                'id': 1,
                'amount': Decimal('123.45'),
                'created': datetime(2026, 2, 4, 12, 0, 0),
                'active': True,
            }
        ],
        query_time_seconds=0.1,
    )

    rows_list = result.to_rows_list()

    assert len(rows_list) == 1
    assert rows_list[0][0] == 1
    assert isinstance(rows_list[0][1], Decimal)
    assert isinstance(rows_list[0][2], datetime)
    assert rows_list[0][3] is True


def test_arango_dict_rows_simulation():
    """Simulate ArangoDB returning list[dict]."""
    aql_result = [
        {'uuid': 'abc-123', 'naam': 'Asset 1', 'toestand': 'actief'},
        {'uuid': 'def-456', 'naam': 'Asset 2', 'toestand': 'reserve'},
    ]

    result = QueryResult(
        keys=list(aql_result[0].keys()) if aql_result else [],
        rows=aql_result,
        query_time_seconds=0.234,
        last_data_update='2026-02-04T12:00:00+00:00',
    )

    assert result.keys == ['uuid', 'naam', 'toestand']
    assert len(result.to_rows_list()) == 2
    assert result.to_rows_list()[0] == ['abc-123', 'Asset 1', 'actief']


def test_postgis_tuple_rows_simulation():
    """Simulate PostGIS returning list[tuple]."""
    cursor_fetchall = [
        ('abc-123', 'Asset 1', 'actief'),
        ('def-456', 'Asset 2', 'reserve'),
    ]
    cursor_description = [
        type('Column', (), {'name': 'uuid'}),
        type('Column', (), {'name': 'naam'}),
        type('Column', (), {'name': 'toestand'}),
    ]

    result = QueryResult(
        keys=[col.name for col in cursor_description],
        rows=cursor_fetchall,
        query_time_seconds=0.123,
        last_data_update='2026-02-04 11:30:00',
    )

    assert result.keys == ['uuid', 'naam', 'toestand']
    assert len(result.to_rows_list()) == 2
    assert result.to_rows_list()[0] == ['abc-123', 'Asset 1', 'actief']


def test_large_resultset_memory_efficiency():
    """Demonstrate memory efficiency of iter_rows vs to_rows_list."""
    import sys

    large_result = QueryResult(
        keys=['id', 'data'],
        rows=[
            {'id': i, 'data': f'Large string data {i}' * 10}
            for i in range(10000)
        ],
        query_time_seconds=2.5,
    )

    # Method 1: to_rows_list (loads all into memory)
    rows_list = large_result.to_rows_list()
    size_list = sys.getsizeof(rows_list)

    # Method 2: iter_rows (streaming, minimal memory)
    row_count = sum(1 for _ in large_result.iter_rows())

    assert row_count == 10000
    assert size_list > 80000  # Significant memory footprint (list object itself)
