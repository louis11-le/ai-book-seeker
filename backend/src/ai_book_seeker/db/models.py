"""
Database Models Module for AI Book Seeker

This module defines SQLAlchemy ORM models for the application's database tables.
It includes the Book model which represents entries in the books table.
"""

from typing import Dict, List, Union

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.mysql import DECIMAL

from .database import Base


class Book(Base):
    """SQLAlchemy model for the books table"""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text)
    from_age = Column(Integer, nullable=True)
    to_age = Column(Integer, nullable=True)
    purpose = Column(Text, nullable=False)
    genre = Column(String(100))
    price = Column(DECIMAL(6, 2), nullable=False)
    tags = Column(Text)

    def to_dict(self) -> Dict[str, Union[int, str, float, List[str]]]:
        """
        Convert model instance to dictionary

        Returns:
            Dictionary with book attributes properly typed
        """
        # Use proper SQLAlchemy attribute access with getattr
        return {
            "id": getattr(self, "id", 0),
            "title": getattr(self, "title", ""),
            "author": getattr(self, "author", ""),
            "description": getattr(self, "description", "") or "",
            "from_age": getattr(self, "from_age", None),
            "to_age": getattr(self, "to_age", None),
            "purpose": getattr(self, "purpose", ""),
            "genre": getattr(self, "genre", "") or "",
            "price": float(getattr(self, "price", 0)) if getattr(self, "price", None) else 0.0,
            "tags": getattr(self, "tags", "").split(",") if getattr(self, "tags", None) else [],
        }
