"""
Enhanced logging configuration for AI Book Seeker.

Provides structured logging with file output, rotation, and environment-based configuration.
Supports both console and file logging with proper error handling.
"""

import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Optional

# Set UTC time for all log timestamps
logging.Formatter.converter = time.gmtime


def setup_logging(
    log_level: str = "INFO",
    environment: str = "development",
    enable_file_logging: bool = False,
    log_directory: str = "./logs",
    log_filename: str = "ai_book_seeker.log",
    error_log_filename: str = "ai_book_seeker_error.log",
    max_file_size_mb: int = 10,
    backup_count: int = 5,
    enable_console_logging: bool = True,
) -> None:
    """
    Setup comprehensive logging configuration with file and console support.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        environment: Environment name for filtering
        enable_file_logging: Whether to enable file logging
        log_directory: Directory for log files
        log_filename: Main log filename
        error_log_filename: Error log filename
        max_file_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
        enable_console_logging: Whether to enable console logging
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

    # Add console handler if enabled
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handlers if file logging is enabled
    if enable_file_logging:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_directory)
            log_path.mkdir(parents=True, exist_ok=True)

            # Main log file with rotation
            main_log_file = log_path / log_filename
            main_handler = logging.handlers.RotatingFileHandler(
                filename=main_log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,  # Convert MB to bytes
                backupCount=backup_count,
                encoding="utf-8",
            )
            main_handler.setLevel(numeric_level)
            main_handler.setFormatter(formatter)
            root_logger.addHandler(main_handler)

            # Error log file (separate file for errors only)
            error_log_file = log_path / error_log_filename
            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            error_handler.setLevel(logging.ERROR)  # Only log errors to this file
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

            # Log successful file logging setup
            root_logger.info(f"File logging enabled: {main_log_file}, errors: {error_log_file}")

        except Exception as e:
            # If file logging fails, log the error but don't crash
            if enable_console_logging:
                print(f"Warning: Failed to setup file logging: {e}")
            else:
                # If console logging is disabled and file logging fails,
                # we need at least one handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(numeric_level)
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)
                print(f"Warning: File logging failed, falling back to console: {e}")

    # Environment-specific logger configurations
    if environment.lower() == "development":
        # Filter out SQLAlchemy logs in development for cleaner output
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    elif environment.lower() == "production":
        # In production, reduce noise from third-party libraries
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.INFO)

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
