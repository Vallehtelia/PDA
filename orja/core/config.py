from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONFIG: Dict[str, Any] = {
    "assistant": {
        "name": "orja",
        "wake_phrase": "hei orja",
        "timezone": "Europe/Helsinki",
    },
    "database": {"path": "data/orja.sqlite"},
    "logging": {"file": "logs/orja.log", "level": "INFO"},
    "llm": {"provider": "local", "model": "placeholder"},
}


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
    merged = {**DEFAULT_CONFIG, **config}
    # Environment variable overrides (flat, prefixed with ORJA_)
    for key, value in os.environ.items():
        if not key.startswith("ORJA_"):
            continue
        conf_key = key.removeprefix("ORJA_").lower()
        # Only override known top-level keys to stay predictable
        if conf_key in merged:
            merged[conf_key] = value
    return merged

