"""Logging setup for scripts and CLI."""

import logging


def configure_logging(level: str = "INFO") -> None:
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        raise TypeError(f"invalid logging level: {level}")
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
