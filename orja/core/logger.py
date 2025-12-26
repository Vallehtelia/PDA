from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


def setup_logger(log_file: Path, level: str = "INFO") -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("orja")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    console_handler = RichHandler(rich_tracebacks=False, markup=True)
    console_handler.setLevel(logger.level)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logger.level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger

