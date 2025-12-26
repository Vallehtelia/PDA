from __future__ import annotations

import re


def timer_skill(command: str) -> str:
    match = re.search(r"(\d+)\s*(min|mins|minuuttia|min|minute)?", command, re.IGNORECASE)
    if match:
        minutes = match.group(1)
        return f"OK, asetin ajastimen {minutes} min (placeholder)."
    return "Ajastinta ei tunnistettu, mutta voin yrittää uudelleen."

