"""
Logging Configuration for AI Book Seeker

This module provides a centralized logging configuration for the entire application.
It sets up appropriate handlers, formatters, and logging levels based on the
environment configuration.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get log level from environment (default to INFO)
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.INFO)

# Log file configuration
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / os.getenv("LOG_FILENAME", "ai-book-seeker.log")
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", "5242880"))  # 5 MB default
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Formatters
VERBOSE_FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
# Updated to include file and line number information
SIMPLE_FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")


def setup_logging():
    """
    Configure the logging for the entire application.
    Sets up console and file handlers with appropriate formatters.
    """
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Clear existing handlers (to avoid duplicate logging in case of reinitialization)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler - for standard output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(SIMPLE_FORMATTER)
    console_handler.setLevel(LOG_LEVEL)

    # File handler - for persistent logs
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    file_handler.setFormatter(VERBOSE_FORMATTER)
    file_handler.setLevel(LOG_LEVEL)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set higher log level for some verbose libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Log setup information
    logging.info(f"Logging initialized at level: {LOG_LEVEL_NAME}")
    logging.info(f"Log file location: {LOG_FILE.absolute()}")


def get_logger(name):
    """
    Get a logger with the specified name.
    This ensures consistent logger naming across the application.

    Args:
        name: The logger name, typically __name__ from the calling module

    Returns:
        A configured logger instance
    """
    return logging.getLogger(f"ai-book-seeker.{name}")
