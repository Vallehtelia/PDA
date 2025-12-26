from __future__ import annotations

from textwrap import shorten
from typing import List

from orja.llm.provider import ChatMessage, LLMProvider


class PlaceholderProvider(LLMProvider):
    """Placeholder LLM provider for development/testing."""

    def generate(
        self,
        messages: List[ChatMessage],
        *,
        system_prompt=None,
        max_tokens=None,
        temperature=None,
        top_p=None,
        json_mode=None,
    ) -> str:
        _ = (system_prompt, max_tokens, temperature, top_p, json_mode)
        user_msg = messages[-1].content if messages else "tuntematon kysymys"
        safe_prompt = shorten(user_msg, width=240, placeholder="...")
        return (
            "Local response (placeholder): "
            f"{safe_prompt} "
            "I can help with basic tasks briefly."
        )

