"""
Utility helper functions for the AI Book Seeker application.
"""

import os
from pathlib import Path
from typing import Union


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
