from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from rich.console import Console

from orja.core.config import load_config
from orja.core.logger import setup_logger
from orja.core.router import Router
from orja.memory.db import MemoryStore

console = Console()


def run() -> None:
    base_path = Path(__file__).resolve().parent.parent
    project_root = base_path.parent

    config_path = project_root / "config" / "config.yaml"
    config = load_config(config_path)

    log_file = project_root / config["logging"]["file"]
    logger = setup_logger(log_file, level=config["logging"].get("level", "INFO"))

    db_path = project_root / config["database"]["path"]
    memory = MemoryStore(db_path)
    router = Router()

    wake_phrase = config["assistant"]["wake_phrase"].lower()
    session_id = f"session-{uuid4()}"
    hint_shown = False

    console.print(f"[bold green]Orja[/bold green] käynnissä. Käytä herätekoodia '{wake_phrase}'.")
    logger.info("Assistant started with session_id=%s", session_id)

    try:
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                console.print("\nHeippa! (EOF)")
                break

            if not user_input:
                continue

            if not user_input.lower().startswith(wake_phrase):
                if not hint_shown:
                    console.print(f"Käytä herätettä '{wake_phrase}' aloittaaksesi.")
                    hint_shown = True
                continue

            command = user_input[len(wake_phrase) :].strip()
            if not command:
                console.print("Mitä haluaisit tehdä?")
                continue

            memory.add_message(
                role="user",
                content=command,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
            )

            try:
                response = router.dispatch(command)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Routing failed: %s", exc)
                response = "Tapahtui virhe. Yritä uudelleen."

            memory.add_message(
                role="assistant",
                content=response,
                session_id=session_id,
                timestamp=datetime.now(timezone.utc),
            )

            console.print(f"[bold cyan]orja:[/bold cyan] {response}")
            logger.info("Handled command: %s", command)

    except KeyboardInterrupt:
        console.print("\nKeskeytettiin. Näkemiin!")
        logger.info("Assistant stopped via KeyboardInterrupt")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Assistant crashed: %s", exc)
        console.print(f"Tapahtui odottamaton virhe: {exc}")
        sys.exit(1)

