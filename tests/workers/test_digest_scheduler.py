from datetime import datetime, timezone

from techpulse.workers.digest_scheduler import last_due_run_utc

_MON_9 = 0, 9


class TestLastDueRunUtc:
    def test_returns_today_when_now_is_after_target_today(self):
        now = datetime(2026, 5, 11, 10, 0, tzinfo=timezone.utc)  # Monday 10:00

        result = last_due_run_utc(now, *_MON_9)

        assert result == datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)

    def test_returns_today_at_target_when_now_equals_target(self):
        now = datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)  # Monday 09:00 sharp

        result = last_due_run_utc(now, *_MON_9)

        assert result == datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)

    def test_returns_previous_week_when_now_is_before_target_today(self):
        now = datetime(2026, 5, 11, 8, 59, tzinfo=timezone.utc)  # Monday 08:59

        result = last_due_run_utc(now, *_MON_9)

        assert result == datetime(2026, 5, 4, 9, 0, tzinfo=timezone.utc)

    def test_returns_previous_monday_when_now_is_midweek(self):
        now = datetime(2026, 5, 13, 15, 30, tzinfo=timezone.utc)  # Wednesday afternoon

        result = last_due_run_utc(now, *_MON_9)

        assert result == datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)

    def test_returns_previous_monday_when_now_is_sunday(self):
        now = datetime(2026, 5, 17, 23, 59, tzinfo=timezone.utc)  # Sunday late

        result = last_due_run_utc(now, *_MON_9)

        assert result == datetime(2026, 5, 11, 9, 0, tzinfo=timezone.utc)

    def test_friday_at_8am_returns_previous_friday_when_dow_is_friday(self):
        now = datetime(2026, 5, 8, 8, 0, tzinfo=timezone.utc)  # Friday 08:00

        result = last_due_run_utc(now, dow=4, hour=9)

        assert result == datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc)

    def test_zeroes_minutes_seconds_microseconds(self):
        now = datetime(2026, 5, 13, 12, 34, 56, 789, tzinfo=timezone.utc)

        result = last_due_run_utc(now, dow=0, hour=9)

        assert result == datetime(2026, 5, 11, 9, 0, 0, 0, tzinfo=timezone.utc)
