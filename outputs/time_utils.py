"""Utilities for parsing and formatting timestamps in Europe/Brussels.

Provides parse_to_brussels(value) -> datetime | None and format_brussels_string(value) -> str
which consistently produce Brussels-aware datetimes or formatted 'YYYY-MM-DD HH:MM:SS' strings.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from zoneinfo import ZoneInfo
from typing import Any

BRUSSELS = ZoneInfo('Europe/Brussels')


def parse_to_brussels(val: Any) -> datetime | None:
    """Parse various timestamp representations to a timezone-aware datetime in Brussels time.

    Accepts: datetime (naive or tz-aware), ISO strings (with or without Z/offset),
    common formats like 'YYYY-MM-DD HH:MM:SS', or None.
    Returns a datetime in Europe/Brussels or None if parsing failed.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        dt = val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BRUSSELS)
        return dt.astimezone(BRUSSELS)

    s = str(val).strip()
    if s == '':
        return None

    # Normalize trailing Z -> +00:00 for fromisoformat
    iso = s.replace('Z', '+00:00') if s.endswith('Z') else s
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BRUSSELS)
        return dt.astimezone(BRUSSELS)
    except Exception:
        pass

    # try a set of common formats
    fmts = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=BRUSSELS)
            return dt.astimezone(BRUSSELS)
        except Exception:
            continue

    # regex fallback: extract first datetime-like substring
    m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?", s)
    if m:
        piece = m.group(0).replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(piece)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=BRUSSELS)
            return dt.astimezone(BRUSSELS)
        except Exception:
            return None

    return None


def format_brussels_string(val: Any) -> str:
    """Format a value as Brussels-local 'YYYY-MM-DD HH:MM:SS'.

    If val is datetime or parseable string, returns formatted Brussels string. If None or
    unparseable, returns empty string.
    """
    if val is None:
        return ''
    if isinstance(val, datetime):
        dt = val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BRUSSELS)
        dt = dt.astimezone(BRUSSELS)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    # attempt parse
    dt = parse_to_brussels(val)
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')

