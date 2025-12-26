from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ChatMessage:
    """A chat message with role and content."""

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[ChatMessage],
        *,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        json_mode: Optional[bool] = None,
    ) -> str:
        """Generate a response from a list of messages."""
        raise NotImplementedError


class ProviderFactory:
    """Factory for creating LLM providers based on configuration."""

    @staticmethod
    def create_provider(config: Dict[str, Any]) -> LLMProvider:
        backend = config.get("backend", "placeholder")

        if backend == "llama_cpp_cli":
            from orja.llm.backends.llama_cpp_cli import LlamaCppCliProvider

            return LlamaCppCliProvider(config)
        if backend == "placeholder":
            from orja.llm.placeholder import PlaceholderProvider

            return PlaceholderProvider()
        raise ValueError(f"Unknown LLM backend: {backend}")

