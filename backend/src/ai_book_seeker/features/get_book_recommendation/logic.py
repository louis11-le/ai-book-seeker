from ai_book_seeker.features.get_book_recommendation.schema import (
    BookRecommendationOutputSchema,
)


def normalize_age_params(request, original_message, extract_age_range_func):
    """
    Normalize age parameters for book recommendation.
    Prefers explicit age_from/age_to, else extracts from message, else falls back to single age.

    Args:
        request: BookRecommendationSchema request object.
        original_message (str): The original user query string.
        extract_age_range_func (callable): Function to extract age range from message.

    Returns:
        tuple: (age_from, age_to) as integers or None.
    """
    age_from = request.age_from
    age_to = request.age_to
    if age_from is None and age_to is None:
        extracted_from, extracted_to = extract_age_range_func(original_message)
        age_from = extracted_from
        age_to = extracted_to
    if age_from is None and age_to is None and request.age is not None:
        age_from = age_to = request.age

    return age_from, age_to


def format_book_recommendation_result(results):
    """
    Format a list of book recommendation results into a BookRecommendationOutputSchema with summary text.

    Args:
        results (list): List of book objects (from DB query).

    Returns:
        BookRecommendationOutputSchema: Output schema with summary text and data list.
    """
    if results:
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
