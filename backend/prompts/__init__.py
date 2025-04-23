"""
Prompt Management Module for AI Book Seeker

This module manages versioned prompts for the application. It provides
functionality for loading prompt templates based on environment variables.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get prompt versions from environment variables
SEARCHER_VERSION = os.getenv("SEARCHER_VERSION", "v1")
EXPLAINER_VERSION = os.getenv("EXPLAINER_VERSION", "v1")
SYSTEM_PROMPT_VERSION = os.getenv("SYSTEM_PROMPT_VERSION", "v1")

# Prompt cache to avoid reading files multiple times
_prompt_cache: Dict[str, str] = {}


def get_prompt_path(prompt_type: str, version: str) -> Path:
    """
    Get the path to a specific prompt file.

    Args:
        prompt_type: The type of prompt (e.g., 'searcher', 'explainer', 'system')
        version: The version of the prompt (e.g., 'v1', 'v2')

    Returns:
        Path to the prompt file
    """
    base_dir = Path(__file__).parent
    if prompt_type == "searcher":
        return base_dir / "searcher" / f"search_books_{version}.txt"
    elif prompt_type == "explainer":
        return base_dir / "explainer" / f"explain_recommendation_{version}.txt"
    elif prompt_type == "system":
        return base_dir / "system" / f"system_prompt_{version}.txt"
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")


def load_prompt(prompt_type: str, version: Optional[str] = None) -> str:
    """
    Load a prompt from a file.

    Args:
        prompt_type: The type of prompt (e.g., 'searcher', 'explainer', 'system')
        version: The version of the prompt (e.g., 'v1', 'v2')
                If None, uses the version from environment variables

    Returns:
        The prompt text
    """
    # Determine the version to use
    if version is None:
        if prompt_type == "searcher":
            version = SEARCHER_VERSION
        elif prompt_type == "explainer":
            version = EXPLAINER_VERSION
        elif prompt_type == "system":
            version = SYSTEM_PROMPT_VERSION
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

    # Create a cache key for this prompt
    cache_key = f"{prompt_type}_{version}"

    # Check if the prompt is already in cache
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    # Get the path to the prompt file
    prompt_path = get_prompt_path(prompt_type, version)

    # Read the prompt file
    try:
        with open(prompt_path, "r") as f:
            prompt = f.read()

        # Cache the prompt
        _prompt_cache[cache_key] = prompt

        return prompt
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")


def get_searcher_prompt() -> str:
    """
    Get the current searcher prompt.

    Returns:
        The searcher prompt text
    """
    return load_prompt("searcher", SEARCHER_VERSION)


def get_explainer_prompt() -> str:
    """
    Get the current explainer prompt.

    Returns:
        The explainer prompt text
    """
    return load_prompt("explainer", EXPLAINER_VERSION)


def get_system_prompt() -> str:
    """
    Get the current system prompt.

    Returns:
        The system prompt text
    """
    return load_prompt("system", SYSTEM_PROMPT_VERSION)
