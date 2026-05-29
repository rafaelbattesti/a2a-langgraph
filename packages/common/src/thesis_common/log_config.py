"""Process-level logging configuration."""

from __future__ import annotations

import logging

from . import config

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
LOG_LEVEL_NAMES = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def parse_log_level(value: str) -> int | None:
    normalized = value.strip().upper()
    if normalized in LOG_LEVEL_NAMES:
        return LOG_LEVEL_NAMES[normalized]
    if normalized.isdecimal():
        return int(normalized)
    return None


def configure_logging() -> None:
    level = parse_log_level(config.LOG_LEVEL)
    if level is None:
        level = logging.INFO
        logging.getLogger(__name__).warning(
            "Invalid LOG_LEVEL %r; falling back to INFO.", config.LOG_LEVEL
        )
    logging.basicConfig(level=level, format=LOG_FORMAT)
