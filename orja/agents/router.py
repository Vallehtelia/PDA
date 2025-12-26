from __future__ import annotations

import logging
from typing import Dict, List, Optional

from orja.agents.utils import parse_json_safely
from orja.core.prompts import PromptLoader
from orja.llm.provider import ChatMessage, LLMProvider


class RouterAgent:
    """Decides whether to call a skill or stay in chat."""

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

    def run(
        self,
        user_text: str,
        available_skills: List[str],
        skill_summaries: str,
    ) -> Dict:
        fallback = {
            "action": "chat",
            "skill": None,
            "arguments": {},
            "confidence": 0.0,
        }
        if not self.enabled:
            return fallback

        system_prompt = self.prompts.get_prompt("router_system")
        skills_line = ", ".join(sorted(available_skills))
        user_prompt = (
            f"Available skills: {skills_line}\n"
            f"Skill descriptions:\n{skill_summaries}\n"
            f"Request: {user_text}\n"
            "Choose a skill or chat. Return JSON only."
        )

        raw = self.provider.generate(
            [ChatMessage(role="user", content=user_prompt)],
            system_prompt=system_prompt,
            max_tokens=self.max_tokens,
            temperature=0.25,
            top_p=0.9,
            json_mode=self.json_mode,
        )
        parsed = parse_json_safely(raw)
        if not parsed:
            self.logger.warning("Router JSON parsing failed, raw=%s", raw)
            return fallback

        action = str(parsed.get("action", "chat")).lower()
        skill = parsed.get("skill")
        if skill not in available_skills:
            skill = None
        arguments: Dict = parsed.get("arguments") if isinstance(parsed.get("arguments"), dict) else {}
        confidence = parsed.get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0
        confidence_value = max(0.0, min(1.0, confidence_value))

        if action not in {"skill", "chat"}:
            action = "chat"
        # Heuristic: if model suggests a valid skill but left action=chat, treat it as skill.
        if skill and action == "chat" and confidence_value >= 0.5:
            action = "skill"
        # If action=skill but skill missing, downgrade to chat.
        if action == "skill" and not skill:
            action = "chat"

        return {
            "action": action,
            "skill": skill,
            "arguments": arguments,
            "confidence": confidence_value,
        }

