from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable

import yaml

DEFAULT_CONFIG: Dict[str, Any] = {
    "assistant": {
        "name": "orja",
        "wake_phrase": "hey slave",
        "timezone": "Europe/Helsinki",
    },
    "dev": {"reload_prompts": True},
    "pipeline": {"enabled": True, "max_history_messages": 6},
    "agents": {
        "evaluator": {"enabled": True, "max_tokens": 80},
        "router": {"enabled": True, "max_tokens": 80},
        "responder": {"enabled": True, "max_tokens": 200},
    },
    "database": {"path": "data/orja.sqlite"},
    "logging": {"file": "logs/orja.log", "level": "INFO"},
    "llm": {
        "backend": "llama_cpp_cli",
        "json_strict": True,
        "system_prompt": (
            "You are Orja, a concise and practical assistant. Reply in English "
            "with brief, helpful answers."
        ),
        "language": "en",
        "history_messages": 6,
        "llama_cpp": {
            "bin_path": "vendor/llama.cpp/build/bin/llama-cli",
            "model_path": "models/SmolLM2-360M-Instruct-Q4_K_M.gguf",
            "threads": 4,
            "ctx_size": 2048,
            "max_tokens": 160,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "batch_size": 256,
            "timeout_sec": 45,
            "server": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 8080,
            },
        },
    },
}


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _set_nested_key(target: Dict[str, Any], keys: Iterable[str], value: Any) -> None:
    keys = list(keys)
    current = target
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    prefix = "ORJA_"
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].lower().split("__")
        _set_nested_key(config, path, value)


def ensure_config_file(config_path: Path) -> None:
    if config_path.exists():
        return
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f, sort_keys=False)


def load_config(config_path: Path) -> Dict[str, Any]:
    ensure_config_file(config_path)
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    merged = merge_dicts(DEFAULT_CONFIG, config)
    _apply_env_overrides(merged)
    return merged

