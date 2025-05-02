"""
Test helpers for the AI Book Seeker application.

This module contains utility functions for testing.
"""

import json
import random
from typing import Dict, List, Optional

from ai_book_seeker.db.models import Book


def create_test_book(
    book_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    publication_year: Optional[int] = None,
    isbn: Optional[str] = None,
    description: Optional[str] = None,
    price: Optional[float] = None,
    genre: Optional[str] = None,
    target_age: Optional[str] = None,
    metadata: Optional[Dict] = None,
    vector_id: Optional[str] = None,
) -> Book:
    """
    Create a test book with the given attributes.

    Args:
        book_id: ID of the book
        title: Title of the book
        author: Author of the book
        publication_year: Year of publication
        isbn: ISBN of the book
        description: Description of the book
        price: Price of the book
        genre: Genre of the book
        target_age: Target age range of the book
        metadata: Additional metadata
        vector_id: ID of the vector embedding

    Returns:
        Book model instance
    """
    # Generate random values for missing fields
    if book_id is None:
        book_id = random.randint(1, 10000)
    if title is None:
        title = f"Test Book {book_id}"
    if author is None:
        author = f"Test Author {book_id}"
    if publication_year is None:
        publication_year = random.randint(1900, 2023)
    if isbn is None:
        isbn = f"ISBN-{book_id}-{random.randint(1000, 9999)}"
    if description is None:
        description = f"This is a test book description for {title}"
    if price is None:
        price = round(random.uniform(5.99, 39.99), 2)
    if genre is None:
        genre = random.choice(["Fiction", "Non-fiction", "Science", "History", "Fantasy"])
    if target_age is None:
        target_age = random.choice(["0-5", "6-12", "13-18", "18+"])
    if metadata is None:
        metadata = {
            "tags": ["test", "sample"],
            "language": "English",
        }
    if vector_id is None:
        vector_id = f"vector-{book_id}"

    # Create and return the book model
    return Book(
        id=book_id,
        title=title,
        author=author,
        publication_year=publication_year,
        isbn=isbn,
        description=description,
        price=price,
        genre=genre,
        target_age=target_age,
        metadata=metadata,
        vector_id=vector_id,
    )


def create_test_books(count: int) -> List[Book]:
    """
    Create a list of test books.

    Args:
        count: Number of test books to create

    Returns:
        List of Book model instances
    """
    return [create_test_book(book_id=i) for i in range(1, count + 1)]


def load_test_data(file_path: str) -> Dict:
    """
    Load test data from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the test data
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
