"""
Logging utilities.
"""
import logging
import sys
from typing import Any, Dict, Optional

import structlog

from baid_server.config import settings


def configure_logging():
    """Configure logging for the application."""
    # Set log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure standard logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer() if settings.ENVIRONMENT != "production" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> Any:
    """
    Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return structlog.get_logger(name)


def get_logger(name: str = "baid_server"):
    """Get a configured logger instance."""
    return logging.getLogger(name)


# --- CORS logging middleware ---
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class CORSMiddlewareLogging(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if origin:
            logger = get_logger()
            logger.info(f"CORS request from origin: {origin} path: {request.url.path}")
        return response

# Usage:
# In main.py, after app creation:
# from baid_server.utils.logging import configure_logging, get_logger, CORSMiddlewareLogging
# configure_logging()
# logger = get_logger()
# app.add_middleware(CORSMiddlewareLogging)