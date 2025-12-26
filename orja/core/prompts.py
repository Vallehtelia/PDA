from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

PROMPT_FILES: Dict[str, str] = {
    "evaluator_system": "evaluator_system.txt",
    "router_system": "router_system.txt",
    "responder_system": "responder_system.txt",
    "skill_summaries": "skill_summaries.txt",
}


class PromptLoader:
    """Loads and hot-reloads prompt files from disk."""

    def __init__(self, prompts_dir: Path, reload_enabled: bool = False) -> None:
        self.prompts_dir = prompts_dir
        self.reload_enabled = reload_enabled
        self.cache: Dict[str, str] = {}
        self.mtimes: Dict[str, float] = {}
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def _prompt_path(self, name: str) -> Path:
        if name not in PROMPT_FILES:
            raise KeyError(f"Tuntematon prompt: {name}")
        return self.prompts_dir / PROMPT_FILES[name]

    def _load_prompt(self, name: str) -> None:
        path = self._prompt_path(name)
        try:
            content = path.read_text(encoding="utf-8")
            self.cache[name] = content
            self.mtimes[name] = path.stat().st_mtime
            logger.debug("Loaded prompt '%s' from %s", name, path)
        except FileNotFoundError:
            logger.warning("Prompt file missing: %s", path)
            self.cache[name] = ""
            self.mtimes[name] = 0.0

    def _load_all(self) -> None:
        for name in PROMPT_FILES:
            self._load_prompt(name)

    def get_prompt(self, name: str) -> str:
        path = self._prompt_path(name)
        if self.reload_enabled:
            try:
                current_mtime = path.stat().st_mtime
            except FileNotFoundError:
                current_mtime = 0.0
            if current_mtime != self.mtimes.get(name):
                self._load_prompt(name)
        return self.cache.get(name, "")

