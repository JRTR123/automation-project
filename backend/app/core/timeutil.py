"""UTC timestamps stored as Unix seconds and shown as ISO-8601."""

from __future__ import annotations

from datetime import datetime, timezone


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def to_iso(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def parse_iso(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("Use an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()
