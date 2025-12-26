from __future__ import annotations

from rich.console import Console

console = Console()


class DummyTTS:
    def speak(self, text: str) -> None:
        console.print(f"[magenta]TTS (placeholder):[/magenta] {text}")

