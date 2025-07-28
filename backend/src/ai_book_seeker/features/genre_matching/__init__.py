"""
Genre matching module for AI Book Seeker

This module provides fuzzy genre matching functionality with synonyms and aliases.
"""

from .constants import GENRE_ALIASES, GENRE_SYNONYMS
from .logic import (
    RAPIDFUZZ_AVAILABLE,
    get_genre_similarity,
    get_matching_stats,
    is_genre_match,
    normalize_genre,
)

__all__ = [
    "normalize_genre",
    "get_genre_similarity",
    "is_genre_match",
    "get_matching_stats",
    "GENRE_SYNONYMS",
    "GENRE_ALIASES",
    "RAPIDFUZZ_AVAILABLE",
]
