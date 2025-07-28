"""
Database connection management for SQLAlchemy.
"""

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from sqlalchemy import create_engine

# Initialize logger
logger = get_logger(__name__)


def create_database_engine(settings: AppSettings):
    """
    Create a SQLAlchemy engine with the provided settings.

    Args:
        settings: Application settings containing database configuration

    Returns:
        Engine: Configured SQLAlchemy engine
    """
    # Use the database connection URL from settings (supports both URL and individual fields)
    database_url = settings.database.get_connection_url()

    # SQLAlchemy setup
    engine = create_engine(
        database_url,
        echo=settings.database.echo_sql,
        pool_pre_ping=True,  # Check connection before using from pool
    )

    return engine
