"""
Canonical Redis client for all non-LangGraph workflow memory usage.

- Use this client for sessions, cache, user/app data, and any application-level Redis needs.
- Do NOT use this client for LangGraph workflow memory or checkpointing. For workflow memory, always use the official
  `langgraph-redis` package (see orchestrator).
- This separation ensures compatibility, maintainability, and best practices as required by project architecture standards.
"""

import redis

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


def create_redis_client(settings: AppSettings) -> redis.Redis:
    """
    Create a Redis client instance using the provided settings.

    Args:
        settings: Application settings containing Redis configuration

    Returns:
        redis.Redis: Configured Redis client instance

    Raises:
        redis.ConnectionError: If connection to Redis fails
    """
    redis_client = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password.get_secret_value() if settings.redis.password else None,
        db=settings.redis.db,
    )

    try:
        redis_client.ping()
        logger.info(f"Redis client connected to {settings.redis.host}:{settings.redis.port}")
        return redis_client
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
        raise
