"""
Test helpers for the AI Book Seeker application.

This module contains utility functions for testing.
"""

import random
from typing import Dict, List, Optional

from ai_book_seeker.db.models import Book


def create_test_book(
    book_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None,
    from_age: Optional[int] = None,
    to_age: Optional[int] = None,
    purpose: Optional[str] = None,
    genre: Optional[str] = None,
    price: Optional[float] = None,
    tags: Optional[str] = None,
    quantity: Optional[int] = None,
) -> Book:
    """
    Create a test Book instance with valid fields only.

    Args:
        book_id: ID of the book
        title: Title of the book
        author: Author of the book
        description: Description of the book
        from_age: Minimum recommended age
        to_age: Maximum recommended age
        purpose: Purpose of the book (learning/entertainment)
        genre: Genre of the book
        price: Price of the book
        tags: Comma-separated tags
        quantity: Inventory quantity

    Returns:
        Book model instance
    """
    if book_id is None:
        book_id = random.randint(1, 10000)
    if title is None:
        title = f"Test Book {book_id}"
    if author is None:
        author = f"Test Author {book_id}"
    if description is None:
        description = f"This is a test book description for {title}"
    if from_age is None:
        from_age = random.choice([6, 8, 10, 12])
    if to_age is None:
        to_age = from_age + random.choice([2, 4, 6])
    if purpose is None:
        purpose = random.choice(["learning", "entertainment"])
    if genre is None:
        genre = random.choice(["Fiction", "Non-fiction", "Science", "History", "Fantasy"])
    if price is None:
        price = round(random.uniform(5.99, 39.99), 2)
    if tags is None:
        tags = "test,book"
    if quantity is None:
        quantity = random.randint(1, 10)

    return Book(
        id=book_id,
        title=title,
        author=author,
        description=description,
        from_age=from_age,
        to_age=to_age,
        purpose=purpose,
        genre=genre,
        price=price,
        tags=tags,
        quantity=quantity,
    )


def create_test_books(count: int) -> List[Book]:
    """
    Create a list of test Book instances.

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
    import json

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
