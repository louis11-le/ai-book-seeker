"""
Database Models Module for AI Book Seeker

This module defines SQLAlchemy ORM models for the application's database tables.
It includes the Book model which represents entries in the books table.
"""

from typing import Dict, List, Union

from sqlalchemy import Column, Enum, Integer, String, Text
from sqlalchemy.dialects.mysql import DECIMAL

from .connection import Base


class Book(Base):
    """SQLAlchemy model for the books table"""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text)
    age_range = Column(String(10), nullable=False)
    purpose: Column = Column(Enum("learning", "entertainment"), nullable=False)
    genre = Column(String(100))
    price = Column(DECIMAL(6, 2), nullable=False)
    tags = Column(Text)
    rating = Column(DECIMAL(2, 1), default=0.0)

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
            "age_range": getattr(self, "age_range", ""),
            "purpose": getattr(self, "purpose", ""),
            "genre": getattr(self, "genre", "") or "",
            "price": float(getattr(self, "price", 0)) if getattr(self, "price", None) else 0.0,
            "tags": getattr(self, "tags", "").split(",") if getattr(self, "tags", None) else [],
            "rating": float(getattr(self, "rating", 0)) if getattr(self, "rating", None) else 0.0,
        }
