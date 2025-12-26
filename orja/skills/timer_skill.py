from __future__ import annotations

import re
from typing import Optional


def _extract_minutes(command: str) -> Optional[str]:
    match = re.search(r"(\d+)\s*(min|mins|minuuttia|min|minute)?", command, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def timer_skill(command: str, minutes: int | None = None) -> str:
    parsed = str(minutes) if minutes is not None else _extract_minutes(command)
    if parsed:
        return f"OK, timer set for {parsed} minutes (placeholder)."
    return "Timer not recognized, please provide the minutes."

