"""Utilities for parsing and formatting timestamps to UTC.

Provides parse_to_utc(value) -> datetime | None and format_utc_string(value) -> str
which consistently produce UTC-aware datetimes or formatted 'YYYY-MM-DD HH:MM:SS' strings.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any


def parse_to_utc(val: Any) -> datetime | None:
    """Parse various timestamp representations to a timezone-aware datetime in UTC.

    Accepts: datetime (naive or tz-aware), ISO strings (with or without Z/offset),
    common formats like 'YYYY-MM-DD HH:MM:SS', or None.
    Returns a datetime in UTC or None if parsing failed.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        dt = val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    s = str(val).strip()
    if s == '':
        return None

    # Normalize trailing Z -> +00:00 for fromisoformat
    iso = s.replace('Z', '+00:00') if s.endswith('Z') else s
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
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
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue

    # regex fallback: extract first datetime-like substring
    m = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?", s)
    if m:
        piece = m.group(0).replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(piece)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    return None


def format_utc_string(val: Any) -> str:
    """Format a value as UTC 'YYYY-MM-DD HH:MM:SS'.

    If val is datetime or parseable string, returns formatted UTC string. If None or
    unparseable, returns empty string.
    """
    if val is None:
        return ''
    if isinstance(val, datetime):
        dt = val
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    # attempt parse
    dt = parse_to_utc(val)
    if dt is None:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')

