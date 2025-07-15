import asyncio

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.services.query import search_books_by_criteria
from ai_book_seeker.utils.helpers import extract_age_range_from_message

from .schema import BookRecommendationOutputSchema, BookRecommendationSchema

logger = get_logger("get_book_recommendation")


async def get_book_recommendation_handler(
    request: BookRecommendationSchema, original_message: str
) -> BookRecommendationOutputSchema:
    """
    Async handler for the get_book_recommendation tool.

    Args:
        request (BookRecommendationSchema): Validated schema with user preferences (age, purpose, budget, genre).
        original_message (str): The original user query string.

    Returns:
        BookRecommendationOutputSchema: Structured response with recommended books and summary text.
    """
    # Prefer explicit age_from/age_to, else extract from message, else fallback to age
    age_from = request.age_from
    age_to = request.age_to
    if age_from is None and age_to is None:
        extracted_from, extracted_to = extract_age_range_from_message(original_message)
        age_from = extracted_from
        age_to = extracted_to

    # If still not set, fallback to single age
    if age_from is None and age_to is None and request.age is not None:
        age_from = age_to = request.age

    purpose = request.purpose
    budget = request.budget
    genre = request.genre

    try:

        def sync_search():
            try:
                with get_db_session() as db:
                    # Pass age_from and age_to to downstream search logic (to be updated in next task)
                    return search_books_by_criteria(
                        db=db,
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
        if results:
            # Standardize output format
            if len(results) == 1:
                book = results[0]
                text = f'I found a great book for you! "{book.title}" by {book.author} is {book.reason} Priced at ${book.price:.2f}.'
            else:
                book_texts = []
                for book in results:
                    book_texts.append(
                        f"Title: {book.title} by {book.author}\nDescription: {book.description}\nPrice: ${book.price:.2f}\nReason: {book.reason}"
                    )
                text = "\n\n".join(book_texts)
        else:
            text = "I couldn't find any books matching your criteria. Could you tell me the age of the reader or what kind of stories you're interested in?"

        return BookRecommendationOutputSchema(text=text, data=results)
    except Exception as e:
        logger.error(f"Internal error in get_book_recommendation_handler: {e}", exc_info=True)
        return BookRecommendationOutputSchema(text="Internal error. Please try again later.", data=[])
