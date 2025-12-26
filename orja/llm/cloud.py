from __future__ import annotations

import logging

logger = logging.getLogger("orja")


class CloudLLM:
    def generate(self, *args, **kwargs):
        logger.warning("CloudLLM is a placeholder and not implemented.")
        raise NotImplementedError("Cloud LLM integration is not implemented yet.")

