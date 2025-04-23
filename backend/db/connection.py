"""
Database Connection Module for AI Book Seeker

This module centralizes database connection management for the application.
It provides SQLAlchemy and Redis client setup and connection pooling.
"""

import os
from typing import Generator

import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from logger import get_logger

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger("db_connection")

# Database configuration
SQLALCHEMY_DATABASE_URL = os.getenv("MYSQL_CONNECTION_STRING", "")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")

# SQLAlchemy setup
# Echo SQL statements in development
echo_sql = os.getenv("ECHO_SQL", "False").lower() == "true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=echo_sql,
    pool_pre_ping=True,  # Check connection before using from pool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Redis client
# Initialize Redis client - this will fail if Redis is unavailable
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    db=int(REDIS_DB),
)

# Test connection to ensure Redis is available
redis_client.ping()
logger.info(f"Redis client connected to {REDIS_HOST}:{REDIS_PORT}")


# Database dependency
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get a database session.

    Yields:
        SQLAlchemy database session

    Notes:
        This is used as a FastAPI dependency to provide database sessions
        to route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
