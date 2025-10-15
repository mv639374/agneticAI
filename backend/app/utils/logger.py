# agenticAI/backend/app/utils/logger.py

"""
Structured Logging Setup using structlog

This module configures structlog for production-grade logging with:
- JSON output for production (easily parsed by log aggregators)
- Human-readable console output for development
- Request ID tracking across async operations
- Automatic exception formatting
- Context-aware logging (attaches metadata to all logs in request scope)

Why structlog over standard logging?
1. Structured data: Logs are key-value pairs, not just strings
2. Context preservation: Metadata follows logs through async operations
3. Performance: Lazy evaluation of log messages
4. Integration: Works seamlessly with FastAPI and async code
"""


import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Remove Uvicorn's color_message field from logs.

    Uvicorn duplicates messages with ANSI color codes, which we don't need in structured logs.
    """

    event_dict.pop("color_message", None)
    return event_dict

def add_app_context(_, __, event_dict: EventDict) -> EventDict:
    """
    Add application-level context to all logs.

    This processor automatically adds:
    - Environment (dev/staging/prod)
    - Application name
    - Service version (if available)

    Useful for:
    - Filtering logs by envronment in centralized logging
    - Identifying service in microservices architecture
    """

    event_dict['environment'] = settings.ENVIRONMENT
    event_dict['app'] = settings.APP_NAME
    return event_dict

def setup_logging() -> None:
    """
    Configure structlog for the application.
    
    This function should be called once at application startup, before any
    logging occurs. It configures both structlog and the standard library
    logging to work together.
    
    Logging Flow:
    1. Structlog captures log with context
    2. Shared processors add metadata (timestamp, log level, etc.)
    3. ProcessorFormatter wraps for standard library compatibility
    4. Final renderer outputs JSON (prod) or console (dev)
    """

    # =========================================================================
    # CONFIGURE SHARED PROCESSORS
    # =========================================================================
    # These processors run on ALL log entries, regardless of source
    
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    shared_processors: list[Processor] = [
        # Merge context variables (request ID, user ID, etc.)
        structlog.contextvars.merge_contextvars,
        
        # Add logger name (e.g., "app.agents.supervisor")
        structlog.stdlib.add_logger_name,
        
        # Add log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structlog.stdlib.add_log_level,
        
        # Format positional arguments in log messages
        structlog.stdlib.PositionalArgumentsFormatter(),
        
        # Add extra fields from logging.LogRecord
        structlog.stdlib.ExtraAdder(),
        
        # Remove Uvicorn's duplicate color message
        drop_color_message_key,
        
        # Add ISO 8601 timestamp
        timestamper,
        
        # Render stack traces for exceptions
        structlog.processors.StackInfoRenderer(),
        
        # Add application context
        add_app_context,
    ]
    
    # =========================================================================
    # CONFIGURE EXCEPTION FORMATTING
    # =========================================================================
    # For JSON logs, format exceptions as structured data
    # For console logs, pretty-print with colors
    
    if settings.LOG_FORMAT == "json":
        shared_processors.append(structlog.processors.format_exc_info)
    
    # =========================================================================
    # CONFIGURE STRUCTLOG
    # =========================================================================
    structlog.configure(
        processors=shared_processors + [
            # Final processor: wrap for standard library compatibility
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # Use standard library LoggerFactory for compatibility
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache logger instances for performance
        cache_logger_on_first_use=True,
    )
    
    # =========================================================================
    # CONFIGURE OUTPUT RENDERER
    # =========================================================================
    # JSON renderer for production (machine-readable)
    # Console renderer for development (human-readable with colors)
    
    log_renderer: structlog.types.Processor
    if settings.LOG_FORMAT == "json":
        log_renderer = structlog.processors.JSONRenderer()
    else:
        log_renderer = structlog.dev.ConsoleRenderer(
            colors=True,  # ANSI color codes
            exception_formatter=structlog.dev.plain_traceback,
        )
    
    # =========================================================================
    # CONFIGURE STANDARD LIBRARY LOGGING
    # =========================================================================
    # This ensures all logs (including from third-party libraries) use structlog
    
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within structlog
        foreign_pre_chain=shared_processors,
        
        # These run on ALL entries after the pre_chain
        processors=[
            # Remove internal structlog metadata
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            
            # Final rendering (JSON or Console)
            log_renderer,
        ],
    )
    
    # =========================================================================
    # SETUP ROOT LOGGER
    # =========================================================================
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL.upper())
    
    # =========================================================================
    # CONFIGURE UVICORN LOGGERS
    # =========================================================================
    # Uvicorn has its own loggers that need special handling
    
    for logger_name in ["uvicorn", "uvicorn.error"]:
        # Clear existing handlers to avoid duplicate logs
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        
        # Propagate to root logger (which uses our structlog formatter)
        uvicorn_logger.propagate = True
    
    # Disable uvicorn.access logger (we'll log requests in middleware)
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    
    # =========================================================================
    # LOG STARTUP MESSAGE
    # =========================================================================
    log = structlog.get_logger()
    log.info(
        "Logging configured",
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        structured=settings.ENABLE_STRUCTURED_LOGGING,
    )


def get_logger(name: str = __name__) -> Any:
    """"
    Get a structlog logger instance.

    Usage:
        from app.utils.logger import get_logger

        log = get_logger(__name__)
        log.info("Processing request", user_id=123, action="login")

    Args:
        name: Logget namee (typically __name__ of the module)

    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Blind context variables to the current async context.

    All subsequent logs in the same async context will include these variables.

    Usage:
        bind_context(request_id="abc-123", user_id=456)
        log.info("User logged in")   # Will include request_id and user_id

    Args:
        **kwargs: Key-value pairs to bind to context
    """

    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """
    Clear all context variables from the current async context.
    
    Typically called at the beginning of each request to prevent context leakage.
    """
    structlog.contextvars.clear_contextvars()
