from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from orja.core.prompts import PromptLoader
from orja.llm.provider import ChatMessage, LLMProvider


class ResponderAgent:
    """Produces the final English reply."""

    def __init__(
        self,
        provider: LLMProvider,
        prompts: PromptLoader,
        agent_config: Dict,
        logger: logging.Logger,
    ) -> None:
        self.provider = provider
        self.prompts = prompts
        self.logger = logger
        self.enabled = agent_config.get("enabled", True)
        self.max_tokens = agent_config.get("max_tokens", 200)

    def run(
        self,
        user_text: str,
        history: List[str],
        evaluation: Dict,
        router_result: Dict,
        skill_output: Optional[str],
    ) -> str:
        if not self.enabled:
            return "Responder is disabled."

        system_prompt = self.prompts.get_prompt("responder_system")
        history_text = "\n".join(history) if history else "no history"
        evaluation_json = json.dumps(evaluation, ensure_ascii=False)
        router_json = json.dumps(router_result, ensure_ascii=False)
        skill_text = skill_output or "no skill result"

        user_prompt = (
            f"User request: {user_text}\n"
            f"Recent messages:\n{history_text}\n"
            f"Evaluation: {evaluation_json}\n"
            f"Routing: {router_json}\n"
            f"Skill result: {skill_text}\n"
            "Generate the final, brief answer in English."
        )

        raw = self.provider.generate(
            [ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            max_tokens=self.max_tokens,
            temperature=0.6,
            top_p=0.9,
        )
        final = raw.strip() or "I could not find an answer, please try again."
        return final

