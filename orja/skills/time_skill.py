from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def time_skill(_: str) -> str:
    tz = ZoneInfo("Europe/Helsinki")
    now_local = datetime.now(tz)
    return f"Kello on {now_local:%H:%M:%S} Suomen aikaa."

