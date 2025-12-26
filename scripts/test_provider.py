#!/usr/bin/env python3
"""
Smoke test for LLM provider.
Tests the provider with a fixed prompt and prints the response.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from orja.core.config import load_config  # noqa: E402
from orja.llm.provider import ChatMessage, ProviderFactory  # noqa: E402


def test_provider() -> bool:
    config_path = project_root / "config" / "config.yaml"
    config = load_config(config_path)

    llm_config = config.get("llm", {})
    provider = ProviderFactory.create_provider(llm_config)

    messages = [ChatMessage(role="user", content="Tell me a short joke in English.")]

    print("Testing LLM provider...")
    print(f"Backend: {llm_config.get('backend', 'unknown')}")
    print(f"Prompt: {messages[0].content}")
    print("-" * 50)

    try:
        response = provider.generate(messages)
        print("Response:")
        print(response)
        print("-" * 50)
        print("✓ Provider test successful")
        return True
    except Exception as exc:  # pragma: no cover - manual smoke test
        print(f"✗ Provider test failed: {exc}")
        return False


if __name__ == "__main__":
    success = test_provider()
    sys.exit(0 if success else 1)

