from datetime import datetime, timedelta, timezone

import pytest

from techpulse.agent.tools._time_window import TimeWindowParseError, parse_time_window

_NOW = datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc)


class TestParseTimeWindow:
    def test_none_returns_none(self):
        assert parse_time_window(None) is None

    def test_empty_string_returns_none(self):
        assert parse_time_window("") is None

    def test_days_shorthand(self):
        assert parse_time_window("7d", now=_NOW) == _NOW - timedelta(days=7)

    def test_weeks_shorthand(self):
        assert parse_time_window("2w", now=_NOW) == _NOW - timedelta(days=14)

    def test_months_shorthand_uses_30_days(self):
        assert parse_time_window("1m", now=_NOW) == _NOW - timedelta(days=30)

    def test_is_case_insensitive(self):
        assert parse_time_window("3D", now=_NOW) == _NOW - timedelta(days=3)

    def test_iso_date_assumes_utc(self):
        result = parse_time_window("2026-05-01")
        assert result == datetime(2026, 5, 1, tzinfo=timezone.utc)

    def test_iso_datetime_preserves_tz(self):
        result = parse_time_window("2026-05-01T08:30:00+02:00")
        assert result == datetime(2026, 5, 1, 8, 30, tzinfo=timezone(timedelta(hours=2)))

    def test_garbage_raises(self):
        with pytest.raises(TimeWindowParseError):
            parse_time_window("last tuesday")
