"""
Logging configuration for the AI Book Seeker application.
"""

import logging
import sys
from typing import Optional

from ai_book_seeker.core.config import LOG_LEVEL

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def get_logger(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance. If no name is provided, returns the root logger.

    Args:
        name: Optional name of the logger (defaults to root logger)
        level: Optional logging level (defaults to LOG_LEVEL from config)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set level from provided level, config, or default to INFO
    log_level = level or LOG_LEVEL or "INFO"
    logger.setLevel(getattr(logging, log_level.upper()))

    # Add handler for console output if not already added
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger
