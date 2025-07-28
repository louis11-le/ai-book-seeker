import asyncio

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.features.get_book_recommendation.logic import (
    format_book_recommendation_result,
    normalize_age_params,
)
from ai_book_seeker.services.query import search_books_by_criteria
from ai_book_seeker.utils.helpers import extract_age_range_from_message

from .schema import BookRecommendationOutputSchema, BookRecommendationSchema

logger = get_logger("get_book_recommendation")


async def get_book_recommendation_handler(
    request: BookRecommendationSchema,
    original_message: str,
    settings: AppSettings,
    chromadb_service=None,
) -> BookRecommendationOutputSchema:
    """
    Async handler for the get_book_recommendation tool.

    Args:
        request (BookRecommendationSchema): Validated schema with user preferences (age, purpose, budget, genre).
        original_message (str): The original user query string.
        settings (AppSettings): Application settings for database configuration.

    Returns:
        BookRecommendationOutputSchema: Structured response with recommended books and summary text.
    """

    purpose = request.purpose
    budget = request.budget
    genre = request.genre
    age_from, age_to = normalize_age_params(request, original_message, extract_age_range_from_message)
    try:

        def sync_search():
            try:
                with get_db_session(settings) as db:
                    # Pass age_from and age_to to downstream search logic (to be updated in next task)
                    return search_books_by_criteria(
                        db=db,
                        chromadb_service=chromadb_service,
                        age_from=age_from,
                        age_to=age_to,
                        purpose=purpose,
                        budget=budget,
                        genre=genre,
                    )
            except Exception as e:
                logger.error(f"Error searching books: {e}", exc_info=True)
                return []

        results = await asyncio.to_thread(sync_search)
        return format_book_recommendation_result(results)
    except Exception as e:
        logger.error(f"Internal error in get_book_recommendation_handler: {e}", exc_info=True)
        return BookRecommendationOutputSchema(text="Internal error. Please try again later.", data=[])
