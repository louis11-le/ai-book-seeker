import logging
import os
import time

logging.Formatter.converter = time.gmtime
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name=None):
    """Get a standard logger by name."""
    return logging.getLogger(name)
