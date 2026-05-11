import re
from datetime import datetime, timedelta, timezone

_RELATIVE_RE = re.compile(r"^\s*(\d+)\s*([dwm])\s*$", re.IGNORECASE)
_UNIT_TO_DAYS = {"d": 1, "w": 7, "m": 30}


class TimeWindowParseError(ValueError):
    pass


def parse_time_window(value: str | None, *, now: datetime | None = None) -> datetime | None:
    if value is None or value == "":
        return None

    reference = now if now is not None else datetime.now(timezone.utc)

    match = _RELATIVE_RE.match(value)
    if match:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        return reference - timedelta(days=amount * _UNIT_TO_DAYS[unit])

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise TimeWindowParseError(
            f"Unrecognised time window {value!r}; expected '7d' / '2w' / '1m' or ISO date like '2026-05-01'."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
