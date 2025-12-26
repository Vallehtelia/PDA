from __future__ import annotations

from typing import Callable, Dict

from orja.llm.local import LocalLLM
from orja.skills.help_skill import help_skill
from orja.skills.time_skill import time_skill
from orja.skills.timer_skill import timer_skill


class Router:
    def __init__(self) -> None:
        self.local_llm = LocalLLM()
        self.intent_map: Dict[str, Callable[[str], str]] = {
            "help": help_skill,
            "apua": help_skill,
            "time": time_skill,
            "aika": time_skill,
        }

    def dispatch(self, command: str) -> str:
        normalized = command.strip()
        lowered = normalized.lower()

        for intent, handler in self.intent_map.items():
            if lowered.startswith(intent):
                return handler(normalized)

        if "ajastin" in lowered or "timer" in lowered:
            return timer_skill(normalized)

        return self.local_llm.generate(normalized)

