"""
Book Explanation Module for AI Book Seeker

This module handles generating personalized explanations for book recommendations
using OpenAI's GPT models.
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from db.models import Book
from logger import get_logger
from prompts import get_explainer_prompt

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger("explainer")

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is required")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Get model from environment
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class BookPreferences(BaseModel):
    """Model representing user preferences for book recommendations"""

    age: Optional[int] = None
    purpose: Optional[str] = None
    budget: Optional[float] = None
    genre: Optional[str] = None
    query_text: Optional[str] = None


def generate_explanations(books: List[Book], preferences: BookPreferences) -> Dict[int, str]:
    """
    Generate explanations for books based on user preferences

    Args:
        books: List of books to generate explanations for
        preferences: User preferences for recommendations

    Returns:
        Dictionary mapping book IDs to explanations
    """
    explanations = {}

    # Process books in batches to reduce API calls
    for i in range(0, len(books), BATCH_SIZE):
        batch = books[i : i + BATCH_SIZE]
        batch_explanations = _generate_batch_explanations(batch, preferences)
        explanations.update(batch_explanations)

    return explanations


def _generate_batch_explanations(books: List[Book], preferences: BookPreferences) -> Dict[int, str]:
    """
    Generate explanations for a batch of books

    Args:
        books: Batch of books to generate explanations for
        preferences: User preferences for recommendations

    Returns:
        Dictionary mapping book IDs to explanations
    """
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
            logger.warning("Empty response from OpenAI API")
            return {}

        # Parse explanations
        return _parse_explanations(content, books)

    except Exception as e:
        logger.error(f"Error generating explanations: {e}")
        return {}


def _create_prompt(books: List[Book], preferences: BookPreferences) -> str:
    """Create prompt for explanation generation"""
    # Format books into text
    books_text = "\n\n".join(
        [
            f"Book ID: {book.id}\nTitle: {book.title}\nAuthor: {book.author}\n"
            f"Age Range: {book.age_range}\nPurpose: {book.purpose}\n"
            f"Description: {book.description or 'No description available'}\n"
            f"Price: ${book.price:.2f}\nTags: {book.tags or 'None'}"
            for book in books
        ]
    )

    # Get the versioned explainer prompt
    base_prompt = get_explainer_prompt()

    # Add book details and preferences to the prompt
    prompt = f"""
    {base_prompt}

    USER PREFERENCES:
    - Age: {preferences.age or 'Any'}
    - Purpose: {preferences.purpose or 'Any'}
    - Budget: ${preferences.budget or 'Any'}
    - Genre: {preferences.genre or 'Any'}
    - Query: {preferences.query_text or 'None'}

    BOOKS TO EVALUATE:
    {books_text}
    """

    return prompt


def _parse_explanations(content: str, books: List[Book]) -> Dict[int, str]:
    """
    Parse explanations from API response

    Args:
        content: Response content from API
        books: List of books

    Returns:
        Dictionary mapping book IDs to explanations
    """
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
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse book ID or explanation from line: {e}")

    return explanations
