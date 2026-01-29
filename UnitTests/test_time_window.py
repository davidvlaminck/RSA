from datetime import datetime
from zoneinfo import ZoneInfo


def _parse_hms_to_seconds(hms: str) -> int:
    parts = (hms or "").split(":")
    if len(parts) != 3:
        raise ValueError
    h, m, s = (int(p) for p in parts)
    return h * 3600 + m * 60 + s


def _is_within_run_window(start_hms: str, end_hms: str, now: datetime) -> bool:
    start_s = _parse_hms_to_seconds(start_hms)
    end_s = _parse_hms_to_seconds(end_hms)
    now_s = now.hour * 3600 + now.minute * 60 + now.second
    if start_s <= end_s:
        return start_s <= now_s <= end_s
    return now_s >= start_s or now_s <= end_s


def test_run_window_boundaries():
    br = ZoneInfo("Europe/Brussels")
    assert _is_within_run_window("03:00:00", "05:50:00", datetime(2026, 1, 21, 2, 59, 59, tzinfo=br)) is False
    assert _is_within_run_window("03:00:00", "05:50:00", datetime(2026, 1, 21, 3, 0, 0, tzinfo=br)) is True
    assert _is_within_run_window("03:00:00", "05:50:00", datetime(2026, 1, 21, 5, 50, 0, tzinfo=br)) is True
    assert _is_within_run_window("03:00:00", "05:50:00", datetime(2026, 1, 21, 5, 50, 1, tzinfo=br)) is False


def test_run_window_cross_midnight():
    br = ZoneInfo("Europe/Brussels")
    # 23:00 -> 02:00 should include 23:30 and 01:30
    assert _is_within_run_window("23:00:00", "02:00:00", datetime(2026, 1, 21, 23, 30, 0, tzinfo=br)) is True
    assert _is_within_run_window("23:00:00", "02:00:00", datetime(2026, 1, 22, 1, 30, 0, tzinfo=br)) is True
    assert _is_within_run_window("23:00:00", "02:00:00", datetime(2026, 1, 22, 12, 0, 0, tzinfo=br)) is False
