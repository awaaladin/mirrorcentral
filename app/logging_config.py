from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Structured-ish logging: one line per record with timestamp, level, and logger name.

    Kept dependency-free (no structlog/json-logger) for phase 1; swap the formatter
    here later if the deploy platform wants JSON lines instead.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Quiet the noisiest third-party loggers down to WARNING regardless of app level.
    for noisy_logger in ("uvicorn.access", "botocore", "boto3"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
