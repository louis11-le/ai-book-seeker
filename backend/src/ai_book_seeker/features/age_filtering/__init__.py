"""
Age filtering module for AI Book Seeker.

This module provides sophisticated age range filtering logic with validation,
error handling, and performance monitoring.
"""

from .logic import AgeFilteringError, apply_age_filters, validate_age_preferences

__all__ = [
    "AgeFilteringError",
    "apply_age_filters",
    "validate_age_preferences",
]
