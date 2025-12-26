from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from orja.agents import EvaluatorAgent, ResponderAgent, RouterAgent
from orja.core.prompts import PromptLoader
from orja.llm.provider import ProviderFactory
from orja.memory.db import MemoryStore, Message
from orja.skills.help_skill import help_skill
from orja.skills.time_skill import time_skill
from orja.skills.timer_skill import timer_skill

logger = logging.getLogger(__name__)


def _truncate(text: str, limit: int = 800) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _extract_minutes(command: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*(min|mins|minuuttia|min|minute)?", command, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


class Pipeline:
    """Runs multi-step agent pipeline for each user request."""

    def __init__(self, memory: MemoryStore, config: Dict, logger_obj: logging.Logger) -> None:
        self.memory = memory
        self.logger = logger_obj
        self.config = config
        self.pipeline_enabled = config.get("pipeline", {}).get("enabled", True)
        self.max_history = config.get("pipeline", {}).get("max_history_messages", 6)
        self.json_mode = config.get("llm", {}).get("json_strict", True)

        base_path = Path(__file__).resolve().parent.parent
        project_root = base_path.parent
        prompts_dir = project_root / "prompts"
        reload_prompts = config.get("dev", {}).get("reload_prompts", False)
        self.prompts = PromptLoader(prompts_dir, reload_enabled=reload_prompts)

        self.provider = ProviderFactory.create_provider(config.get("llm", {}))

        agents_cfg = config.get("agents", {})
        self.evaluator = EvaluatorAgent(
            self.provider,
            self.prompts,
            agents_cfg.get("evaluator", {}),
            logger_obj,
            json_mode=self.json_mode,
        )
        self.router = RouterAgent(
            self.provider,
            self.prompts,
            agents_cfg.get("router", {}),
            logger_obj,
            json_mode=self.json_mode,
        )
        self.responder = ResponderAgent(
            self.provider, self.prompts, agents_cfg.get("responder", {}), logger_obj
        )

        self.skill_functions = {
            "help": help_skill,
            "time": time_skill,
            "timer": timer_skill,
        }
        self.manual_prefixes = {
            "help": ("help", "commands", "what can you do"),
            "time": ("time", "clock", "what time", "what's the time", "whats the time", "current time"),
        }

    def _record_event(
        self,
        session_id: str,
        step_name: str,
        input_summary: str,
        output_data: str,
        success: bool,
        latency_ms: Optional[float],
    ) -> None:
        try:
            self.memory.add_pipeline_event(
                session_id=session_id,
                step_name=step_name,
                input_summary=_truncate(input_summary, 400),
                output_json=_truncate(output_data, 1000),
                success=success,
                latency_ms=latency_ms,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to persist pipeline event %s: %s", step_name, exc)

    def _run_evaluator(self, user_text: str, history: List[str], session_id: str) -> Dict:
        start = time.perf_counter()
        result = self.evaluator.run(user_text, history)
        latency = (time.perf_counter() - start) * 1000
        self.logger.info(
            "Evaluator result: %s (%.1f ms)", json.dumps(result, ensure_ascii=False), latency
        )
        self._record_event(
            session_id,
            "evaluator",
            input_summary=user_text,
            output_data=json.dumps(result, ensure_ascii=False),
            success=True,
            latency_ms=latency,
        )
        return result

    def _manual_router(self, command: str) -> Optional[Dict]:
        lowered = command.strip().lower()
        for skill, prefixes in self.manual_prefixes.items():
            for prefix in prefixes:
                if lowered.startswith(prefix):
                    return {
                        "action": "skill",
                        "skill": skill,
                        "arguments": {},
                        "confidence": 1.0,
                        "source": "manual",
                    }
        if "timer" in lowered or "countdown" in lowered or "alarm" in lowered:
            minutes = _extract_minutes(command)
            args = {"minutes": minutes} if minutes is not None else {}
            return {
                "action": "skill",
                "skill": "timer",
                "arguments": args,
                "confidence": 0.9,
                "source": "manual",
            }
        return None

    def _run_router(self, user_text: str, session_id: str) -> Dict:
        manual = self._manual_router(user_text)
        if manual:
            self._record_event(
                session_id,
                "router_manual",
                input_summary=user_text,
                output_data=json.dumps(manual, ensure_ascii=False),
                success=True,
                latency_ms=0.0,
            )
            return manual

        start = time.perf_counter()
        skill_summaries = self.prompts.get_prompt("skill_summaries")
        result = self.router.run(
            user_text=user_text,
            available_skills=list(self.skill_functions.keys()),
            skill_summaries=skill_summaries,
        )
        if result.get("skill") == "timer":
            arguments = result.get("arguments") or {}
            if arguments.get("minutes") is None:
                minutes = _extract_minutes(user_text)
                if minutes is not None:
                    arguments["minutes"] = minutes
                    result["arguments"] = arguments
        latency = (time.perf_counter() - start) * 1000
        self.logger.info(
            "Router result: %s (%.1f ms)", json.dumps(result, ensure_ascii=False), latency
        )
        self._record_event(
            session_id,
            "router",
            input_summary=user_text,
            output_data=json.dumps(result, ensure_ascii=False),
            success=True,
            latency_ms=latency,
        )
        return result

    def _run_skill(self, skill_name: str, arguments: Dict, user_text: str, session_id: str) -> str:
        start = time.perf_counter()
        handler = self.skill_functions.get(skill_name)
        if not handler:
            return "Skill not found."

        try:
            if skill_name == "timer":
                minutes = arguments.get("minutes")
                result = handler(user_text, minutes=minutes)
            else:
                result = handler(user_text)
            success = True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Skill %s failed: %s", skill_name, exc)
            result = "Skill execution failed."
            success = False

        latency = (time.perf_counter() - start) * 1000
        self._record_event(
            session_id,
            f"skill_{skill_name}",
            input_summary=user_text,
            output_data=result,
            success=success,
            latency_ms=latency,
        )
        return result

    def _run_responder(
        self,
        user_text: str,
        history: List[str],
        evaluation: Dict,
        router_result: Dict,
        skill_output: Optional[str],
        session_id: str,
    ) -> str:
        start = time.perf_counter()
        result = self.responder.run(
            user_text=user_text,
            history=history,
            evaluation=evaluation,
            router_result=router_result,
            skill_output=skill_output,
        )
        latency = (time.perf_counter() - start) * 1000
        self._record_event(
            session_id,
            "responder",
            input_summary=user_text,
            output_data=result,
            success=True,
            latency_ms=latency,
        )
        return result

    def _history_strings(self, messages: List[Message]) -> List[str]:
        ordered = list(reversed(messages))  # oldest first
        return [f"{m.role}: {m.content}" for m in ordered]

    def handle_user_request(self, user_text: str, session_id: str) -> str:
        if not self.pipeline_enabled:
            return "Pipeline is disabled."

        try:
            recent_messages = self.memory.recent_messages(
                limit=self.max_history, session_id=session_id
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Unable to load history: %s", exc)
            recent_messages = []

        history_strings = self._history_strings(recent_messages)

        try:
            evaluation = self._run_evaluator(user_text, history_strings, session_id)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Evaluator step failed: %s", exc)
            evaluation = {"difficulty": "medium", "needs_cloud": False, "reason": "error"}
            self._record_event(
                session_id,
                "evaluator",
                input_summary=user_text,
                output_data=str(exc),
                success=False,
                latency_ms=None,
            )

        try:
            router_result = self._run_router(user_text, session_id)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Router step failed: %s", exc)
            router_result = {"action": "chat", "skill": None, "arguments": {}, "confidence": 0.0}
            self._record_event(
                session_id,
                "router",
                input_summary=user_text,
                output_data=str(exc),
                success=False,
                latency_ms=None,
            )

        skill_output: Optional[str] = None
        if router_result.get("action") == "skill" and router_result.get("skill") in self.skill_functions:
            arguments = router_result.get("arguments") or {}
            skill_output = self._run_skill(
                router_result["skill"], arguments, user_text, session_id
            )

        try:
            response = self._run_responder(
                user_text,
                history_strings,
                evaluation,
                router_result,
                skill_output,
                session_id,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Responder step failed: %s", exc)
            response = "An error occurred while generating the response."
            self._record_event(
                session_id,
                "responder",
                input_summary=user_text,
                output_data=str(exc),
                success=False,
                latency_ms=None,
            )

        return response

