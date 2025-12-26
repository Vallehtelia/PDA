from __future__ import annotations

from textwrap import shorten


class LocalLLM:
    def generate(self, prompt: str) -> str:
        safe_prompt = shorten(prompt, width=240, placeholder="...")
        return (
            "Paikallinen vastaus (placeholder): "
            f"{safe_prompt} "
            "Voin auttaa perusasioissa lyhyesti."
        )

