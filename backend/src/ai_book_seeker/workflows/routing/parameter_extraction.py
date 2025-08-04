"""
Parameter extraction logic for workflow orchestration.

This module contains the logic for extracting parameters from user queries.
Follows LangGraph best practices for parameter extraction.
"""

import json
import re

from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


async def extract_parameters_with_llm(query: str, llm) -> dict:
    """
    Extract parameters from user query using LLM.

    Args:
        query: User query string
        llm: Language model for extraction (required - no fallback)

    Returns:
        dict: Extracted parameters for all tools

    Raises:
        ValueError: If LLM extraction fails - no fallback mechanism
    """
    try:
        extraction_prompt = f"""
        Extract parameters from the following user query for book recommendation and FAQ tools.

        Query: "{query}"

        Extract parameters for:
        1. FAQ Tool: faq_query (the question or topic)
        2. Book Recommendation Tool: age, genre, budget, purpose
        3. Book Details Tool: title, author, isbn

        Return a JSON object with the following structure:
        {{
            "faq_query": "extracted FAQ question or topic",
            "age": number or null,  # Single age - use null for age ranges
            "age_from": number or null,  # Start of age range - use null for single ages
            "age_to": number or null,  # End of age range - use null for single ages
            "genre": "extracted genre",
            "budget": number or null,
            "purpose": "extracted purpose",
            "title": "extracted book title",
            "author": "extracted author name",
            "isbn": "extracted ISBN"
        }}

        AGE RANGE HANDLING:
        - For single ages: Set "age" field, leave "age_from" and "age_to" as null
          Examples: "for a 10-year-old" → age: 10, age_from: null, age_to: null
        - For age ranges: Set "age_from" and "age_to", leave "age" as null
          Examples:
          * "between 1 and 6" → age: null, age_from: 1, age_to: 6
          * "ages 1-6" → age: null, age_from: 1, age_to: 6
          * "1 to 6 years old" → age: null, age_from: 1, age_to: 6
          * "for children 1-6" → age: null, age_from: 1, age_to: 6

        Only include parameters that are actually mentioned in the query.
        Use null for missing parameters.
        """

        response = await llm.ainvoke(extraction_prompt, response_format={"type": "json_object"})

        logger.info(f"Extracted parameters: {response.content}")
        extracted_params = json.loads(response.content)

        # Validate and clean parameters
        return _validate_and_clean_parameters(extracted_params)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"LLM parameter extraction failed: {e}")
        raise ValueError(f"Failed to extract parameters with LLM: {e}")
    except Exception as e:
        logger.error(f"Parameter extraction failed: {e}")
        raise ValueError(f"Parameter extraction failed: {e}")


def _validate_and_clean_parameters(params: dict) -> dict:
    """
    Validate and clean extracted parameters.

    Args:
        params: Raw extracted parameters

    Returns:
        dict: Cleaned and validated parameters
    """
    cleaned = {}

    # FAQ query
    if "faq_query" in params:
        cleaned["faq_query"] = _safe_string(params["faq_query"])

    # Age validation
    if "age" in params and params["age"] is not None:
        age = _safe_int(params["age"])
        if 0 <= age <= 120:  # Reasonable age range
            cleaned["age"] = age

    # Age range validation
    if "age_from" in params and params["age_from"] is not None:
        age_from = _safe_int(params["age_from"])
        if 0 <= age_from <= 120:  # Reasonable age range
            cleaned["age_from"] = age_from

    if "age_to" in params and params["age_to"] is not None:
        age_to = _safe_int(params["age_to"])
        if 0 <= age_to <= 120:  # Reasonable age range
            cleaned["age_to"] = age_to

    # Validate age range consistency
    if "age_from" in cleaned and "age_to" in cleaned:
        if cleaned["age_from"] > cleaned["age_to"]:
            # Swap if from > to
            cleaned["age_from"], cleaned["age_to"] = cleaned["age_to"], cleaned["age_from"]

    # Genre validation
    if "genre" in params:
        cleaned["genre"] = _safe_string(params["genre"])

    # Budget validation
    if "budget" in params and params["budget"] is not None:
        budget = _safe_float(params["budget"])
        if budget >= 0:  # Non-negative budget
            cleaned["budget"] = budget

    # Purpose validation
    if "purpose" in params:
        cleaned["purpose"] = _safe_string(params["purpose"])

    # Title validation
    if "title" in params:
        cleaned["title"] = _safe_string(params["title"])

    # Author validation
    if "author" in params:
        cleaned["author"] = _safe_string(params["author"])

    # ISBN validation
    if "isbn" in params:
        isbn = _safe_string(params["isbn"])
        # Basic ISBN validation (10 or 13 digits)
        if re.match(r"^\d{10,13}$", isbn):
            cleaned["isbn"] = isbn

    return cleaned


def _safe_int(value) -> int:
    """Safely convert value to integer, handling age ranges and plus signs."""
    if value is None:
        return 0

    # Convert to string for processing
    value_str = str(value).strip()

    # Handle age ranges like "16+", "16-18", "16 to 18"
    if "+" in value_str:
        # Extract the number before the plus sign
        match = re.match(r"(\d+)\+?", value_str)
        if match:
            return int(match.group(1))

    # Handle ranges like "16-18", "16 to 18", "16-18 years"
    if "-" in value_str or " to " in value_str:
        # Extract the first number in the range
        match = re.match(r"(\d+)", value_str)
        if match:
            return int(match.group(1))

    # Handle plain numbers
    try:
        return int(value_str)
    except (ValueError, TypeError):
        return 0


def _safe_float(value) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_string(value) -> str:
    """Safely convert value to string."""
    if value is None:
        return ""
    return str(value).strip()


def _safe_list(value) -> list:
    """Safely convert value to list."""
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        return [value]
    else:
        return []
