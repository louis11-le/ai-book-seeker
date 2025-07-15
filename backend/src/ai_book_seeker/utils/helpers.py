"""
Utility helper functions for the AI Book Seeker application.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple, Union


def load_text_file(file_path: Union[str, Path]) -> str:
    """
    Load the contents of a text file.

    Args:
        file_path: Path to the text file

    Returns:
        The contents of the text file as a string
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory

    Returns:
        Path object for the directory
    """
    path = Path(directory)
    os.makedirs(path, exist_ok=True)
    return path


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length, adding ellipsis if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def extract_age_range_from_message(message: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extracts age range or comparison from a natural language message.
    Handles:
    - Ranges: 'from 16 to 31', '16-31', '16 to 31'
    - Less than/under: 'under 33', 'less than 33', 'below 33'
    - Greater than/over: 'over 33', 'more than 33', 'above 33'
    - Single age: 'age 16', '16 year old', etc.
    Returns (age_from, age_to)
    """
    # Range: "from 16 to 31", "16-31", "16 to 31"
    match = re.search(r"(?:from\s*)?(\d{1,2})\s*(?:-|to|–)\s*(\d{1,2})", message, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Less than/under/below
    match = re.search(r"(?:under|less than|below)\s*(\d{1,2})", message, re.IGNORECASE)
    if match:
        return None, int(match.group(1)) - 1

    # Greater than/over/above/more than
    match = re.search(r"(?:over|more than|above)\s*(\d{1,2})", message, re.IGNORECASE)
    if match:
        return int(match.group(1)) + 1, None

    # Single age
    match = re.search(r"age\s*(\d{1,2})|(\d{1,2})\s*(?:year[- ]?old)", message, re.IGNORECASE)
    if match:
        age = int(match.group(1) or match.group(2))
        return age, age

    return None, None
