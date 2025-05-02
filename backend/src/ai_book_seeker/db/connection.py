"""
Database connection management for Redis and SQLAlchemy.
"""

import os

import redis
from sqlalchemy import create_engine

from ai_book_seeker.core.config import DATABASE_URL, REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from ai_book_seeker.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Redis client
# Initialize Redis client - this will fail if Redis is unavailable
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    db=int(REDIS_DB),
)

# Test connection to ensure Redis is available
try:
    redis_client.ping()
    logger.info(f"Redis client connected to {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    raise

# SQLAlchemy setup
# Echo SQL statements in development
echo_sql = os.getenv("ECHO_SQL", "False").lower() == "true"

engine = create_engine(
    DATABASE_URL,
    echo=echo_sql,
    pool_pre_ping=True,  # Check connection before using from pool
)
