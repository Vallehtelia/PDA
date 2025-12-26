from __future__ import annotations

import logging
from typing import Dict, List

from orja.agents.utils import parse_json_safely
from orja.llm.provider import ChatMessage, LLMProvider
from orja.core.prompts import PromptLoader


class EvaluatorAgent:
    """Estimates difficulty and potential cloud need."""

    def __init__(
        self,
        provider: LLMProvider,
        prompts: PromptLoader,
        agent_config: Dict,
        logger: logging.Logger,
        json_mode: bool = False,
    ) -> None:
        self.provider = provider
        self.prompts = prompts
        self.logger = logger
        self.enabled = agent_config.get("enabled", True)
        self.max_tokens = agent_config.get("max_tokens", 80)
        self.json_mode = json_mode

    def run(self, user_text: str, recent_context: List[str]) -> Dict:
        fallback = {
            "difficulty": "medium",
            "needs_cloud": False,
            "reason": "skip",
        }
        if not self.enabled:
            return fallback

        system_prompt = self.prompts.get_prompt("evaluator_system")
        context_text = "\n".join(recent_context) if recent_context else "no history"
        user_prompt = (
            "Evaluate the request difficulty and whether cloud might be needed later.\n"
            f"Request: {user_text}\n"
            f"Short context:\n{context_text}\n"
            "Respond with only a JSON object."
        )

        raw = self.provider.generate(
            [ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            max_tokens=self.max_tokens,
            temperature=0.2,
            top_p=0.9,
            json_mode=self.json_mode,
        )
        parsed = parse_json_safely(raw)
        if not parsed:
            self.logger.warning("Evaluator JSON parsing failed, raw=%s", raw)
            return {**fallback, "reason": "parse_failed"}

        difficulty = str(parsed.get("difficulty", "medium")).lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"
        needs_cloud = bool(parsed.get("needs_cloud", False))
        reason = str(parsed.get("reason", "")).strip() or "no reason provided"

        return {
            "difficulty": difficulty,
            "needs_cloud": needs_cloud,
            "reason": reason,
        }

