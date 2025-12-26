from __future__ import annotations


class DummySTT:
    def transcribe(self, audio_input: str) -> str:
        # Placeholder: simply returns the provided "audio" text.
        return audio_input

