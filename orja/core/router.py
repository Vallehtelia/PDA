from __future__ import annotations

from typing import Callable, Dict, TYPE_CHECKING

from orja.llm.provider import ChatMessage, ProviderFactory
from orja.skills.help_skill import help_skill
from orja.skills.time_skill import time_skill
from orja.skills.timer_skill import timer_skill

if TYPE_CHECKING:
    from orja.memory.db import MemoryStore


class Router:
    def __init__(self, memory: "MemoryStore", config: Dict) -> None:
        self.memory = memory
        self.llm_config = config.get("llm", {})
        self.provider = ProviderFactory.create_provider(self.llm_config)
        self.intent_map: Dict[str, Callable[[str], str]] = {
            "help": help_skill,
            "time": time_skill,
        }

    def dispatch(self, command: str) -> str:
        normalized = command.strip()
        lowered = normalized.lower()

        for intent, handler in self.intent_map.items():
            if lowered.startswith(intent):
                return handler(normalized)

        if "timer" in lowered or "countdown" in lowered:
            return timer_skill(normalized)

        history_limit = self.llm_config.get("history_messages", 6)
        recent_db_messages = self.memory.recent_messages(limit=history_limit)

        chat_messages = []
        for db_msg in reversed(recent_db_messages):
            chat_messages.append(ChatMessage(role=db_msg.role, content=db_msg.content))
        chat_messages.append(ChatMessage(role="user", content=command))

        return self.provider.generate(chat_messages)

