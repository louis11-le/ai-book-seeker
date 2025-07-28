"""
Book query logic for AI Book Seeker

This module handles querying the database for books based on various criteria.
All configuration is accessed via AppSettings for consistency.
"""

from typing import Any, List, Optional

from sqlalchemy.orm import Session

from ai_book_seeker.core.config import create_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book
from ai_book_seeker.features.age_filtering import AgeFilteringError, apply_age_filters
from ai_book_seeker.features.budget_optimization import filter_by_budget
from ai_book_seeker.features.genre_matching import RAPIDFUZZ_AVAILABLE, is_genre_match
from ai_book_seeker.features.get_book_recommendation.schema import BookRecommendation
from ai_book_seeker.features.vector_search import supplement_with_vector_search
from ai_book_seeker.services.explainer import BookPreferences, generate_explanations

logger = get_logger(__name__)

# Default values
DEFAULT_MAX_BOOKS = 10


def _apply_filters(query, preferences: BookPreferences):
    """
    Apply SQL filters for age, purpose, and genre to the book query.

    Args:
        query: SQLAlchemy query object for Book
        preferences: BookPreferences object with user criteria

    Returns:
        Filtered SQLAlchemy query object

    Note:
        This function applies filters in the following order:
        1. Age range filters (age_from/age_to or single age)
        2. Purpose filter (exact match)
        3. Genre filter (fuzzy matching if RapidFuzz available, else exact match)

    Age Range Logic:
        - For single age: Book should be suitable for the user's age
        - For age range: Book's age range should overlap with user's range
        - Books with null age ranges are considered suitable for all ages
    """
    try:
        # Apply age filters with correct business logic and validation
        query = apply_age_filters(query, preferences, Book)
    except AgeFilteringError as e:
        logger.error(f"Age filtering error: {e}", exc_info=True)
        # Return empty result for invalid age preferences
        return query.filter(Book.id.is_(None))
    except ValueError as e:
        logger.error(f"Invalid input for age filtering: {e}", exc_info=True)
        # Return empty result for invalid inputs
        return query.filter(Book.id.is_(None))

    if preferences.purpose is not None:
        query = query.filter(Book.purpose == preferences.purpose.lower())

    if preferences.genre is not None:
        if RAPIDFUZZ_AVAILABLE:
            # Use fuzzy genre matching
            # First, get all books and filter by genre in Python
            # This is less efficient but allows for fuzzy matching
            all_books = query.all()
            genre_matched_books = [book for book in all_books if is_genre_match(preferences.genre, book.genre)]

            # Return a new query with the matched book IDs
            if genre_matched_books:
                book_ids = [book.id for book in genre_matched_books]
                query = query.filter(Book.id.in_(book_ids))
            else:
                # No genre matches found
                query = query.filter(Book.id.is_(None))  # Empty result
        else:
            # Fallback to exact matching
            query = query.filter(Book.genre.like(f"%{preferences.genre.lower()}%"))

    # Log the generated SQL query for debugging
    logger.info(f"Generated SQL query: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}")
    return query


def search_books_by_criteria(
    db: Session,
    chromadb_service: Any,
    age: Optional[int] = None,
    age_from: Optional[int] = None,
    age_to: Optional[int] = None,
    purpose: Optional[str] = None,
    budget: Optional[float] = None,
    genre: Optional[str] = None,
    query_text: Optional[str] = None,
) -> List[BookRecommendation]:
    """
    Search for books based on various criteria.

    Args:
        db: Database session
        chromadb_service: ChromaDB service instance
        age: Target age (single age)
        age_from: Minimum age
        age_to: Maximum age
        purpose: Book purpose (learning, entertainment, etc.)
        budget: Maximum budget
        genre: Book genre
        query_text: Additional search text

    Returns:
        List of BookRecommendation objects
    """
    # Validate inputs - return empty list for invalid inputs
    if age is not None and (age < 0 or age > 120):
        logger.warning(f"Invalid age: {age}. Age must be between 0 and 120.")
        return []

    if age_from is not None and (age_from < 0 or age_from > 120):
        logger.warning(f"Invalid age_from: {age_from}. Age must be between 0 and 120.")
        return []

    if age_to is not None and (age_to < 0 or age_to > 120):
        logger.warning(f"Invalid age_to: {age_to}. Age must be between 0 and 120.")
        return []

    if age_from is not None and age_to is not None and age_from > age_to:
        logger.warning(f"Invalid age range: age_from ({age_from}) cannot be greater than age_to ({age_to})")
        return []

    if budget is not None and budget < 0:
        logger.warning(f"Invalid budget: {budget}. Budget cannot be negative.")
        return []

    # Create preferences object
    preferences = BookPreferences(
        age=age,
        age_from=age_from,
        age_to=age_to,
        purpose=purpose,
        budget=budget,
        genre=genre,
        query_text=query_text,
    )

    # Search for books
    books = search_books(db, preferences, chromadb_service)

    return books


def search_books(db: Session, preferences: BookPreferences, chromadb_service: Any) -> List[BookRecommendation]:
    """
    Search for books based on preferences.

    Args:
        db: Database session
        preferences: BookPreferences object
        chromadb_service: ChromaDB service instance

    Returns:
        List of BookRecommendation objects
    """
    try:
        # Start with all books
        query = db.query(Book)

        # Apply filters
        query = _apply_filters(query, preferences)

        # Execute query
        books = query.all()

        # Supplement with vector search if needed
        books = supplement_with_vector_search(books, preferences, db, DEFAULT_MAX_BOOKS, chromadb_service)

        # Apply budget filtering
        books = filter_by_budget(books, preferences.budget)

        # Limit results
        books = books[:DEFAULT_MAX_BOOKS]

        # Generate explanations
        explanations = generate_explanations(books, preferences, create_settings())

        # Convert books to BookRecommendation objects
        recommendations = []
        for book in books:
            recommendation = BookRecommendation(
                id=book.id,
                title=book.title,
                author=book.author or "",
                description=book.description or "",
                from_age=book.from_age,
                to_age=book.to_age,
                purpose=book.purpose or "",
                genre=book.genre or "",
                price=float(book.price) if book.price else 0.0,
                tags=book.tags.split(",") if book.tags else [],
                quantity=book.quantity or 0,
                reason=explanations.get(book.id, f"This book is perfect for {preferences.age or 'all ages'}!"),
            )
            recommendations.append(recommendation)

        logger.info(f"Found {len(recommendations)} book recommendations")
        return recommendations
    except Exception as e:
        logger.error(f"Error in search_books: {e}", exc_info=True)
        return []
