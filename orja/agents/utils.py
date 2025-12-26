from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def parse_json_safely(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extract first JSON object from model output. Returns None on failure."""
    if not raw_text:
        return None

    cleaned = raw_text.strip()
    # Strip common code fences
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        if cleaned.endswith("```"):
            cleaned = cleaned[: cleaned.rfind("```")]
    # Find JSON object boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        logger.debug("No JSON object found in output: %s", cleaned[:200])
        return None

    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        logger.debug("JSON parsing failed: %s | text=%s", exc, snippet[:200])
        return None

