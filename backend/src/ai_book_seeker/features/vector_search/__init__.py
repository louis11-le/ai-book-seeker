"""
Vector search module for AI Book Seeker

This module provides vector search supplementation functionality with performance
monitoring, analytics, and enhanced error handling.
"""

from .logic import get_vector_search_stats, supplement_with_vector_search

__all__ = [
    "supplement_with_vector_search",
    "get_vector_search_stats",
]
