"""
Book query logic for AI Book Seeker

This module handles querying the database for books based on various criteria.
"""

from typing import List, Optional

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book
from ai_book_seeker.features.get_book_recommendation.schema import BookRecommendation
from ai_book_seeker.services.explainer import BookPreferences, generate_explanations
from ai_book_seeker.services.vectordb import get_book_vector_matches, search_by_vector
from sqlalchemy.orm import Session

# Set up logging
logger = get_logger("query")


def search_books_by_criteria(
    db: Session,
    age: Optional[int] = None,
    age_from: Optional[int] = None,
    age_to: Optional[int] = None,
    purpose: Optional[str] = None,
    budget: Optional[float] = None,
    genre: Optional[str] = None,
    query_text: Optional[str] = None,
) -> List[BookRecommendation]:
    """
    Search for books in the database based on criteria.

    Args:
        db: SQLAlchemy database session
        age: Optional age of the reader (single value)
        age_from: Optional starting age if a range is specified
        age_to: Optional ending age if a range is specified
        purpose: Optional purpose of the book (learning/entertainment)
        budget: Optional maximum price
        genre: Optional genre to filter by
        query_text: Optional semantic search query text

    Returns:
        List of BookRecommendation models matching the criteria, with explanations
    """
    logger.info(
        "search_books_by_criteria called: age=%s, age_from=%s, age_to=%s, purpose=%s, budget=%s, genre=%s, query_text=%s",
        age,
        age_from,
        age_to,
        purpose,
        budget,
        genre,
        query_text,
    )
    preferences = BookPreferences(
        age=age, age_from=age_from, age_to=age_to, purpose=purpose, budget=budget, genre=genre, query_text=query_text
    )
    try:
        results = search_books(db, preferences)
        logger.info(f"search_books_by_criteria results: count={len(results)}, titles={[r.title for r in results]}")
        return results
    except Exception as e:
        logger.error(f"Error in search_books_by_criteria: {e}", exc_info=True)
        return []


def search_books(db: Session, preferences: BookPreferences) -> List[BookRecommendation]:
    """
    Search for books in the database based on user preferences.

    Workflow:
    1. If preferences.query_text is provided, perform a semantic vector search to get
       relevant book IDs.
    2. Build a SQLAlchemy query for Book, optionally filtering by the vector search results.
    3. Apply additional SQL filters for age, purpose, and genre.
    4. Execute the SQL query with a limit (max_suggestion_book).
    5. If the SQL results are insufficient, supplement with vector search results
       (avoiding duplicates).
    6. Filter the combined results by budget, if specified.
    7. Generate personalized explanations for each recommended book.
    8. Return a list of book dictionaries, each with an explanation.
    """

    # If query text is provided, first try semantic search
    book_ids = []
    logger.info(f"search_books preferences: {preferences}")
    if preferences.query_text:
        logger.info(f"Performing semantic search with query: {preferences.query_text}")
        book_ids = search_by_vector(preferences.query_text)

    query = db.query(Book)
    if book_ids:
        query = query.filter(Book.id.in_(book_ids))

    query = _apply_filters(query, preferences)
    max_suggestion_book = 3
    books = query.limit(max_suggestion_book).all()
    logger.info(f"SQL query returned {len(books)} books: {[b.title for b in books]}")

    books = _supplement_with_vector_search(books, preferences, db, max_suggestion_book)
    logger.info(f"After vector supplement: {len(books)} books: {[b.title for b in books]}")

    books = _filter_by_budget(books, preferences.budget)
    logger.info(
        f"After budget filter: {len(books)} books: {[b.title for b in books]}, prices: {[b.price for b in books]}"
    )

    if books:
        explanations = generate_explanations(books, preferences)
        result = []

        for book in books:
            book_dict = book.to_dict()
            age_phrase = "suitable for readers of all ages"
            if book.from_age is not None and book.to_age is not None:
                age_phrase = f"suitable for ages {book.from_age}-{book.to_age}"

            # Build the default explanation
            default_explanation = f"This book is {age_phrase} and focuses on {book.purpose}."

            # Convert the book ID to int and look up any custom explanation
            book_id_int = int(book.id)
            custom_explanation = explanations.get(book_id_int)

            # Assign either the custom explanation (if it exists) or the default one
            book_dict["reason"] = default_explanation
            if custom_explanation is not None:
                book_dict["reason"] = custom_explanation

            try:
                result.append(BookRecommendation(**book_dict))
            except Exception as e:
                logger.error(f"Error creating BookRecommendation model: {e}, data: {book_dict}", exc_info=True)

        return result

    return []


def _apply_filters(query, preferences):
    """
    Apply SQL filters for age, purpose, and genre to the book query.

    Args:
        query: SQLAlchemy query object for Book
        preferences: BookPreferences object with user criteria

    Returns:
        Filtered SQLAlchemy query object
    """
    # Prefer age_from/age_to, else age
    if preferences.age_from is not None or preferences.age_to is not None:
        if preferences.age_from is not None and preferences.age_to is not None:
            # Book's age range must be entirely within the user-specified range
            query = query.filter(
                (Book.from_age.is_(None) | (Book.from_age >= preferences.age_from))
                & (Book.to_age.is_(None) | (Book.to_age <= preferences.age_to))
            )
        elif preferences.age_from is not None:
            query = query.filter(Book.from_age.is_(None) | (Book.from_age >= preferences.age_from))
        elif preferences.age_to is not None:
            query = query.filter(Book.to_age.is_(None) | (Book.to_age <= preferences.age_to))
    elif preferences.age is not None:
        age = preferences.age
        query = query.filter(
            ((Book.from_age.is_(None) | (Book.from_age <= age)) & (Book.to_age.is_(None) | (Book.to_age >= age)))
            | (Book.from_age.is_(None) & Book.to_age.is_(None))
        )

    if preferences.purpose is not None:
        query = query.filter(Book.purpose == preferences.purpose.lower())

    if preferences.genre is not None:
        query = query.filter(Book.genre.like(f"%{preferences.genre.lower()}%"))

    # Log the generated SQL query for debugging
    logger.info(f"Generated SQL query: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}")
    return query


def _supplement_with_vector_search(books, preferences, db, max_suggestion_book):
    """
    Supplement SQL results with vector search if not enough books are found.

    Args:
        books: List of Book objects from SQL query
        preferences: BookPreferences object with user criteria
        db: SQLAlchemy database session
        max_suggestion_book: Maximum number of books to return

    Returns:
        List of Book objects, supplemented with vector search results if needed
    """
    if len(books) >= max_suggestion_book:
        return books

    logger.debug("Supplementing with vector search due to insufficient SQL results")
    # Build search_query to match the content_to_embed format used in embeddings
    search_parts = []
    # Prefer age_from/age_to, else age
    if preferences.age_from is not None and preferences.age_to is not None:
        search_parts.append(f"Age range: {preferences.age_from}-{preferences.age_to}")
    elif preferences.age is not None:
        search_parts.append(f"Age range: {preferences.age}")

    if preferences.purpose is not None:
        search_parts.append(f"Purpose: {preferences.purpose}")

    if preferences.genre is not None:
        search_parts.append(f"Genre: {preferences.genre}")

    # Optionally add query_text if available
    if preferences.query_text:
        search_parts.append(f"Description: {preferences.query_text}")

    search_query = " | ".join(search_parts)
    if not search_query:
        return books

    vector_results = get_book_vector_matches(search_query, db, limit=max_suggestion_book * 2)
    all_books = {book.id: book for book in books}
    for book in vector_results:
        if book.id not in all_books and len(all_books) < max_suggestion_book:
            all_books[book.id] = book

    return list(all_books.values())


def _filter_by_budget(books, budget):
    """
    Filter books by budget, returning those that fit within the specified budget.

    Args:
        books: List of Book objects
        budget: Maximum total budget (float or None)

    Returns:
        List of Book objects that fit within the budget
    """
    if budget is None:
        return books

    books = sorted(books, key=lambda b: float(b.price) if b.price else 0.0)
    budget_remaining = budget
    budget_books = []

    for book in books:
        book_price = float(book.price) if book.price else 0.0
        if book_price <= budget_remaining:
            budget_books.append(book)
            budget_remaining -= book_price

    if not budget_books and books:
        cheapest_book = min(books, key=lambda b: float(b.price) if b.price else 0.0)
        if float(cheapest_book.price) <= budget:
            budget_books = [cheapest_book]

    return budget_books
