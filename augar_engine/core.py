from __future__ import annotations

import calendar
import re
from datetime import datetime, timezone
from typing import Any, Dict

from .schemas import PeriodRef

PERIOD_RE = re.compile(r"^(?P<year>\d{4})-(?P<unit>\d{2})-(?P<freq>[WMQY])$")
TIMESTAMP_RE = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})[-T](?P<hour>\d{2}):?(?P<minute>\d{2})$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_period() -> PeriodRef:
    now = datetime.now(timezone.utc)
    pid = now.strftime("%Y-%m-%d-%H%M")
    label = now.strftime("%Y-%m-%d %H:%M UTC")
    return PeriodRef(id=pid, label=label, freq="T")


def parse_period(period: str) -> PeriodRef:
    period = str(period).strip()
    # Timestamp format: YYYY-MM-DD-HHMM or YYYY-MM-DD-HH:MM
    tm = TIMESTAMP_RE.match(period)
    if tm:
        label = f"{tm['year']}-{tm['month']}-{tm['day']} {tm['hour']}:{tm['minute']} UTC"
        pid = f"{tm['year']}-{tm['month']}-{tm['day']}-{tm['hour']}{tm['minute']}"
        return PeriodRef(id=pid, label=label, freq="T")
    # Legacy format: YYYY-MM-FREQ
    match = PERIOD_RE.match(period)
    if match:
        year = int(match.group("year"))
        unit = int(match.group("unit"))
        freq = match.group("freq")
        if freq == "M":
            if unit < 1 or unit > 12:
                raise ValueError("monthly period month must be 01-12")
            label = f"{calendar.month_name[unit]} {year}"
        elif freq == "Q":
            if unit < 1 or unit > 4:
                raise ValueError("quarterly period unit must be 01-04")
            label = f"Q{unit} {year}"
        elif freq == "W":
            if unit < 1 or unit > 53:
                raise ValueError("weekly period unit must be 01-53")
            label = f"Week {unit}, {year}"
        else:
            if unit != 1:
                raise ValueError("yearly period must use YYYY-01-Y")
            label = str(year)
        return PeriodRef(id=period, label=label, freq=freq)
    raise ValueError("period must be YYYY-MM-DD-HHMM (timestamp) or YYYY-MM-FREQ (e.g. 2026-04-M)")


def stable_seed(*parts: Any) -> int:
    text = "|".join(str(p) for p in parts)
    value = 2166136261
    for char in text:
        value ^= ord(char)
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def scrub_secrets(data: Dict[str, Any]) -> Dict[str, Any]:
    secret_words = ("key", "token", "secret", "password", "authorization", "auth_path", "codex_home", "codex_path")
    clean: Dict[str, Any] = {}
    for key, value in data.items():
        if any(word in str(key).lower() for word in secret_words):
            clean[key] = "***"
        elif isinstance(value, dict):
            clean[key] = scrub_secrets(value)
        else:
            clean[key] = value
    return clean
