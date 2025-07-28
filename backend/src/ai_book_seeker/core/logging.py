"""
Simple logging configuration for AI Book Seeker.

Provides structured logging with correlation IDs and environment-based configuration.
Keeps logging simple and focused.
"""

import logging
import sys
import time
from typing import Optional

# Set UTC time for all log timestamps
logging.Formatter.converter = time.gmtime


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """
    Setup simple logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        environment: Environment name for filtering
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter with timestamp, filename, line number, and structured data support
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s:%(filename)s:%(lineno)d - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Filter out SQLAlchemy logs in development for cleaner output
    if environment.lower() == "development":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a standard logger by name for structured logging.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger instance
    """

    return logging.getLogger(name)
