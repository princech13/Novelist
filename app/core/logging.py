"""Structured logging configuration using structlog.

Call ``configure_logging()`` once at application startup.

* In production (LOG_LEVEL != DEBUG): JSON lines emitted to stdout — machine-readable,
  easy to ingest into Splunk, CloudWatch, or any log aggregator.
* In development (LOG_LEVEL == DEBUG): colourised, aligned console output via
  structlog's ConsoleRenderer for human readability.

All modules should obtain a logger with::

    import structlog
    logger = structlog.get_logger(__name__)

The bound context key ``logger`` carries the dotted module name so log lines
are always traceable back to their source.
"""
import logging
import sys

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    is_development = log_level.upper() == "DEBUG"

    # --- stdlib root logger ---------------------------------------------------
    # structlog forwards to stdlib; set the root level here so stdlib handlers
    # (e.g. uvicorn) respect the same threshold.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # --- shared processors ----------------------------------------------------
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_development:
        # Human-readable, coloured output in the terminal
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # Machine-readable JSON lines for production log aggregators
        shared_processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove any handlers that basicConfig installed so we don't double-log.
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
