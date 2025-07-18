"""
Book Explanation Module for AI Book Seeker

This module handles generating personalized explanations for book recommendations
using OpenAI's GPT models.
"""

from typing import Dict, List, Optional

from ai_book_seeker.core.config import (
    BATCH_SIZE,
    OPENAI_API_KEY,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
)
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book
from ai_book_seeker.prompts import get_explainer_prompt
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger(__name__)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class BookPreferences(BaseModel):
    """Model representing user preferences for book recommendations"""

    age: Optional[int] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    purpose: Optional[str] = None
    budget: Optional[float] = None
    genre: Optional[str] = None
    query_text: Optional[str] = None


def strip_markdown(text: str) -> str:
    """Remove markdown formatting from a string (bold, italics, etc.)."""
    import re

    # Remove bold (**text** or __text__)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    # Remove italics (*text* or _text_)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    # Remove inline code (`text`)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Remove bullet points and extra asterisks
    text = re.sub(r"^\s*[-*]+\s*", "", text, flags=re.MULTILINE)
    return text


def generate_explanations(books: List[Book], preferences: BookPreferences) -> Dict[int, str]:
    """
    Generate explanations for books based on user preferences
    """
    logger.info(f"generate_explanations called: num_books={len(books)}, preferences={preferences.dict()}")
    explanations = {}

    # Process books in batches to reduce API calls
    for i in range(0, len(books), BATCH_SIZE):
        batch = books[i : i + BATCH_SIZE]
        batch_explanations = _generate_batch_explanations(batch, preferences)
        # Strip markdown from all explanations
        batch_explanations = {k: strip_markdown(v) for k, v in batch_explanations.items()}
        explanations.update(batch_explanations)

    logger.info(
        f"generate_explanations completed: num_explanations={len(explanations)}, book_ids={list(explanations.keys())}"
    )
    return explanations


def _generate_batch_explanations(books: List[Book], preferences: BookPreferences) -> Dict[int, str]:
    logger.info(f"_generate_batch_explanations called: batch_size={len(books)}, preferences={preferences.dict()}")
    try:
        # Create prompt for explanation generation
        prompt = _create_prompt(books, preferences)

        # Call API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
        )

        content = response.choices[0].message.content
        if not content:
            logger.info("_generate_batch_explanations: Empty response from OpenAI API")
            return {}

        # Parse explanations
        return _parse_explanations(content, books)

    except Exception as e:
        logger.error(f"Error generating explanations: {e}", exc_info=True)
        # Return a fallback explanation for each book in the batch, only for books with a valid int id
        return {book.id: "Fallback explanation." for book in books if isinstance(book.id, int)}


def _create_prompt(books: List[Book], preferences: BookPreferences) -> str:
    """Create prompt for explanation generation"""
    # Format books into text
    books_text = "\n\n".join(
        [
            f"Book ID: {book.id}\nTitle: {book.title}\nAuthor: {book.author}\n"
            f"Age Range: {f'{book.from_age}-{book.to_age}' if book.from_age is not None and book.to_age is not None else 'All ages'}\n"
            f"Purpose: {book.purpose}\n"
            f"Description: {book.description or 'No description available'}\n"
            f"Price: ${book.price:.2f}\nTags: {book.tags or 'None'}"
            for book in books
        ]
    )

    # Get the versioned explainer prompt
    base_prompt = get_explainer_prompt()

    # Add book details and preferences to the prompt
    # Prefer age_from/age_to, else age, else 'Any'
    if preferences.age_from is not None and preferences.age_to is not None:
        age_str = f"{preferences.age_from}-{preferences.age_to}"
    elif preferences.age is not None:
        age_str = str(preferences.age)
    else:
        age_str = "Any"

    prompt = f"""
    {base_prompt}

    USER PREFERENCES:
    - Age: {age_str}
    - Purpose: {preferences.purpose or 'Any'}
    - Budget: ${preferences.budget or 'Any'}
    - Genre: {preferences.genre or 'Any'}
    - Query: {preferences.query_text or 'None'}

    BOOKS TO EVALUATE:
    {books_text}
    """
    # logger.info(f"_create_prompt: prompt_length={len(prompt)}, preview={prompt[:200].replace(chr(10), ' ')}...")
    return prompt


def _parse_explanations(content: str, books: List[Book]) -> Dict[int, str]:
    logger.info(f"_parse_explanations called: content_length={len(content)}, num_books={len(books)}")
    explanations = {}
    book_ids = {book.id for book in books}

    # Try multiple parsing approaches to handle different response formats
    # Handle multi-line format with [BOOK_ID:id] and [/BOOK_ID] tags
    if "[/BOOK_ID]" in content:
        sections = content.split("[BOOK_ID:")
        for section in sections[1:]:  # Skip the first split which is before any tag
            try:
                # Extract the book ID
                id_end = section.find("]")
                if id_end == -1:
                    continue

                book_id = int(section[:id_end].strip())

                # Extract the explanation text between the tags
                explanation_text = section[id_end + 1 : section.find("[/BOOK_ID]")].strip()

                # Only add explanations for valid book IDs
                if book_id in book_ids:
                    explanations[book_id] = explanation_text
                    logger.info(f"book_id: {book_id}, explanation text: {explanation_text}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse multi-line explanation: {e}")

    # If no explanations found yet, try to handle consecutive [BOOK_ID:id] format
    if not explanations and "[BOOK_ID:" in content:
        try:
            # Split by [BOOK_ID: to get individual explanations
            parts = content.split("[BOOK_ID:")
            for part in parts[1:]:  # Skip the first empty part
                # Find the end of the book ID
                id_end = part.find("]")
                if id_end == -1:
                    continue

                # Extract the book ID
                book_id = int(part[:id_end].strip())

                # Extract the explanation text
                explanation_start = id_end + 1

                # Find the next [BOOK_ID: if it exists
                next_book = part.find("[BOOK_ID:", explanation_start)
                if next_book == -1:
                    # This is the last explanation
                    explanation = part[explanation_start:].strip()
                else:
                    # Extract until the next book ID
                    explanation = part[explanation_start:next_book].strip()

                # Only add explanations for valid book IDs
                if book_id in book_ids:
                    explanations[book_id] = explanation
                    logger.info(f"book_id: {book_id}, explanation: {explanation}")
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse consecutive book ID format: {e}")

    # If still no explanations, try the simple single-line format as a fallback
    if not explanations:
        lines = content.strip().split("\n")
        for line in lines:
            # Check for the [BOOK_ID:id] format
            if line.startswith("[BOOK_ID:") and "]" in line:
                try:
                    # Extract book ID and explanation
                    id_part = line.split("]")[0].replace("[BOOK_ID:", "").strip()
                    book_id = int(id_part)
                    explanation = line.split("]", 1)[1].strip()

                    # Only add explanations for valid book IDs
                    if book_id in book_ids:
                        explanations[book_id] = explanation
                        logger.info(f"book_id: {book_id}, explanation: {explanation}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse book ID or explanation from line: {e}")

    logger.info(
        f"_parse_explanations completed: num_explanations={len(explanations)}, book_ids={list(explanations.keys())}"
    )

    return explanations
