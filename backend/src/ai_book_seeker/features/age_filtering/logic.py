"""
Age filtering logic for AI Book Seeker.

This module provides sophisticated age range filtering logic with comprehensive
validation, error handling, and performance monitoring.

Business Rules:
- Single age: Book.from_age <= user_age <= Book.to_age (or no restrictions)
- Age range: Book's range overlaps with user's range (or no restrictions)
- Age_from only: Book.to_age >= age_from (or no upper limit)
- Age_to only: Book.from_age <= age_to (or no lower limit)
- Books with null age ranges are suitable for all ages
- Age values must be between 0 and 120
- age_from must be <= age_to when both are specified
- Mutual exclusivity: cannot specify both 'age' and 'age_from'/'age_to'

Performance Characteristics:
- Time Complexity: O(1) - adds SQL filters only
- Space Complexity: O(1) - no additional data structures
- Validation Overhead: <1ms for typical inputs
- Performance Monitoring: <0.1ms overhead per function call
"""

import time
from functools import wraps
from typing import List, Optional, Protocol

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.explainer import BookPreferences
from sqlalchemy import Column, and_, or_
from sqlalchemy.orm import Query

logger = get_logger(__name__)

# Configuration Constants
MIN_AGE = 0
MAX_AGE = 120
PERFORMANCE_THRESHOLD_MS = 100  # 100ms threshold for performance warnings


class BookModelProtocol(Protocol):
    """Protocol defining the required interface for book models.

    This protocol ensures type safety when working with different book model
    implementations while maintaining loose coupling.
    """

    from_age: Column[int]
    to_age: Column[int]


class AgeFilteringError(Exception):
    """Custom exception for age filtering errors.

    Provides specific error handling for age-related validation and processing
    failures, enabling graceful degradation and detailed error reporting.
    """

    pass


def monitor_performance(func):
    """Decorator to monitor function performance and log slow operations.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function with performance monitoring

    Performance Impact:
        - Overhead: <0.1ms per function call
        - Logging: Debug level for normal operations, Warning for slow operations
        - Threshold: Configurable via PERFORMANCE_THRESHOLD_MS constant
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        if execution_time > PERFORMANCE_THRESHOLD_MS:
            logger.warning(
                f"Slow age filtering: {func.__name__} took {execution_time:.2f}ms "
                f"(threshold: {PERFORMANCE_THRESHOLD_MS}ms)"
            )
        else:
            logger.debug(f"Age filtering: {func.__name__} took {execution_time:.2f}ms")

        return result

    return wrapper


def validate_age_preferences(preferences: Optional[BookPreferences]) -> List[str]:
    """
    Validate age preferences and return list of validation errors.

    Performs comprehensive validation of age-related preferences including:
    - Type validation (integers only)
    - Range validation (0-120)
    - Business rule validation (age_from <= age_to)
    - Mutual exclusivity validation (age vs age_from/age_to)

    Args:
        preferences: User preferences to validate (can be None)

    Returns:
        List of validation error messages (empty if valid)

    Examples:
        >>> prefs = BookPreferences(age=10)
        >>> errors = validate_age_preferences(prefs)
        >>> assert len(errors) == 0

        >>> prefs = BookPreferences(age_from=15, age_to=10)
        >>> errors = validate_age_preferences(prefs)
        >>> assert len(errors) == 1
        >>> assert "age_from (15) cannot be greater than age_to (10)" in errors[0]
    """
    if not preferences:
        return []

    errors = []

    # Validate single age
    if preferences.age is not None:
        if not isinstance(preferences.age, int):
            errors.append(f"Age must be an integer, got {type(preferences.age).__name__}")
        elif not (MIN_AGE <= preferences.age <= MAX_AGE):
            errors.append(f"Age must be between {MIN_AGE} and {MAX_AGE}, got {preferences.age}")

    # Validate age_from
    if preferences.age_from is not None:
        if not isinstance(preferences.age_from, int):
            errors.append(f"Age_from must be an integer, got {type(preferences.age_from).__name__}")
        elif not (MIN_AGE <= preferences.age_from <= MAX_AGE):
            errors.append(f"Age_from must be between {MIN_AGE} and {MAX_AGE}, got {preferences.age_from}")

    # Validate age_to
    if preferences.age_to is not None:
        if not isinstance(preferences.age_to, int):
            errors.append(f"Age_to must be an integer, got {type(preferences.age_to).__name__}")
        elif not (MIN_AGE <= preferences.age_to <= MAX_AGE):
            errors.append(f"Age_to must be between {MIN_AGE} and {MAX_AGE}, got {preferences.age_to}")

    # Validate business rule: age_from <= age_to
    if preferences.age_from is not None and preferences.age_to is not None:
        if preferences.age_from > preferences.age_to:
            errors.append(
                f"Business rule violation: age_from ({preferences.age_from}) "
                f"cannot be greater than age_to ({preferences.age_to})"
            )

    # Validate mutual exclusivity: age vs age_from/age_to
    if preferences.age is not None and (preferences.age_from is not None or preferences.age_to is not None):
        errors.append(
            "Mutual exclusivity violation: cannot specify both 'age' and 'age_from'/'age_to' "
            "simultaneously. Use either single age or age range."
        )

    return errors


@monitor_performance
def apply_age_filters(
    query: Query, preferences: Optional[BookPreferences], book_model: type[BookModelProtocol]
) -> Query:
    """
    Apply age filters with correct business logic and comprehensive validation.

    This function implements sophisticated age range filtering that handles
    various user preference scenarios while maintaining optimal performance.

    The function applies filters in the following order:
    1. Input validation (query type, book model interface)
    2. Age preference validation (range, business rules, mutual exclusivity)
    3. Age range filtering (age_from/age_to combinations)
    4. Single age filtering (exact age match)
    5. Early return for null preferences

    Args:
        query: SQLAlchemy query object for Book model
        preferences: User preferences containing age criteria (can be None)
        book_model: SQLAlchemy Book model class (injected to avoid circular imports)

    Returns:
        Filtered SQLAlchemy query object

    Raises:
        AgeFilteringError: If validation fails or invalid inputs are provided
        ValueError: If book_model is invalid

    Examples:
        >>> # Single age filtering
        >>> prefs = BookPreferences(age=10)
        >>> filtered = apply_age_filters(query, prefs, Book)

        >>> # Age range filtering
        >>> prefs = BookPreferences(age_from=7, age_to=12)
        >>> filtered = apply_age_filters(query, prefs, Book)

        >>> # Age_from only
        >>> prefs = BookPreferences(age_from=15)
        >>> filtered = apply_age_filters(query, prefs, Book)

        >>> # Null preferences (no filtering)
        >>> filtered = apply_age_filters(query, None, Book)

    Performance:
        - Time Complexity: O(1) - adds SQL filters only
        - Space Complexity: O(1) - no additional data structures
        - Database Impact: Minimal - leverages SQLAlchemy query optimization
        - Validation Overhead: <1ms for typical inputs
    """
    # Validate inputs
    if not isinstance(query, Query):
        raise ValueError(f"Query must be a SQLAlchemy Query object, got {type(query).__name__}")

    if not hasattr(book_model, "from_age") or not hasattr(book_model, "to_age"):
        raise ValueError("Book model must have 'from_age' and 'to_age' attributes")

    # Early return for null preferences
    if not preferences:
        logger.debug("No age preferences provided, returning unfiltered query")
        return query

    # Validate age preferences
    validation_errors = validate_age_preferences(preferences)
    if validation_errors:
        error_message = "Age preference validation failed:\n" + "\n".join(f"- {error}" for error in validation_errors)
        logger.error(error_message)
        raise AgeFilteringError(error_message)

    try:
        # Handle age_from/age_to combinations first (more specific)
        if preferences.age_from is not None or preferences.age_to is not None:
            logger.debug(f"Applying age range filters: age_from={preferences.age_from}, age_to={preferences.age_to}")
            return _apply_age_range_filters(query, preferences, book_model)

        # Handle single age case
        elif preferences.age is not None:
            logger.debug(f"Applying single age filter: age={preferences.age}")
            return _apply_single_age_filter(query, preferences.age, book_model)

        # No age preferences specified
        logger.debug("No specific age preferences, returning unfiltered query")
        return query

    except Exception as e:
        logger.error(f"Error applying age filters: {e}", exc_info=True)
        raise AgeFilteringError(f"Failed to apply age filters: {str(e)}")


@monitor_performance
def _apply_age_range_filters(query: Query, preferences: BookPreferences, book_model: type[BookModelProtocol]) -> Query:
    """
    Apply filters for age range scenarios (age_from/age_to combinations).

    Routes to appropriate filter function based on which age parameters are specified:
    - Both age_from and age_to: Full age range overlap
    - Only age_from: Minimum age requirement
    - Only age_to: Maximum age requirement

    Args:
        query: SQLAlchemy query object
        preferences: User preferences with age_from/age_to
        book_model: SQLAlchemy Book model class

    Returns:
        Filtered SQLAlchemy query object
    """
    if preferences.age_from is not None and preferences.age_to is not None:
        # Full age range: Book's range should overlap with user's range
        return _apply_full_age_range_filter(query, preferences.age_from, preferences.age_to, book_model)

    elif preferences.age_from is not None:
        # Age_from only: Book should be suitable for age_from and above
        return _apply_age_from_filter(query, preferences.age_from, book_model)

    elif preferences.age_to is not None:
        # Age_to only: Book should be suitable for age_to and below
        return _apply_age_to_filter(query, preferences.age_to, book_model)

    return query


@monitor_performance
def _apply_full_age_range_filter(
    query: Query, age_from: int, age_to: int, book_model: type[BookModelProtocol]
) -> Query:
    """
    Apply filter for full age range (both age_from and age_to specified).

    Business Logic: Book's age range must overlap with user's range.
    A book for ages 8-12 will match a user asking for ages 7-10 (overlap).

    The filter includes books that:
    1. Have no age restrictions (suitable for all ages)
    2. Have age ranges that overlap with the user's specified range

    Args:
        query: SQLAlchemy query object
        age_from: Minimum user age
        age_to: Maximum user age
        book_model: SQLAlchemy Book model class

    Returns:
        Filtered SQLAlchemy query object

    Examples:
        >>> # User wants ages 7-10
        >>> # Book ages 8-12: ✅ Overlaps (8 <= 10 and 12 >= 7)
        >>> # Book ages 5-8: ✅ Overlaps (5 <= 10 and 8 >= 7)
        >>> # Book ages 12-15: ❌ No overlap (12 > 10)
    """
    logger.debug(f"Applying full age range filter: {age_from}-{age_to}")

    return query.filter(
        or_(
            # Book has no age restrictions (suitable for all ages)
            and_(book_model.from_age.is_(None), book_model.to_age.is_(None)),
            # Book's age range overlaps with user's range
            and_(
                or_(book_model.from_age.is_(None), book_model.from_age <= age_to),
                or_(book_model.to_age.is_(None), book_model.to_age >= age_from),
            ),
        )
    )


@monitor_performance
def _apply_age_from_filter(query: Query, age_from: int, book_model: type[BookModelProtocol]) -> Query:
    """
    Apply filter for age_from only (minimum age requirement).

    Business Logic: Book should be suitable for age_from and above.
    A book for ages 12-18 will match a user asking for age 15+.

    The filter includes books that:
    1. Have no upper age limit (suitable for all ages)
    2. Have an upper age limit that extends to or beyond the user's minimum age

    Args:
        query: SQLAlchemy query object
        age_from: Minimum user age
        book_model: SQLAlchemy Book model class

    Returns:
        Filtered SQLAlchemy query object

    Examples:
        >>> # User wants age 15+
        >>> # Book ages 12-18: ✅ Suitable (18 >= 15)
        >>> # Book ages 5-12: ❌ Not suitable (12 < 15)
        >>> # Book ages 16+: ✅ Suitable (no upper limit)
    """
    logger.debug(f"Applying age_from filter: {age_from} and above")

    return query.filter(
        or_(
            book_model.to_age.is_(None),  # No upper age limit
            book_model.to_age >= age_from,
        )
    )


@monitor_performance
def _apply_age_to_filter(query: Query, age_to: int, book_model: type[BookModelProtocol]) -> Query:
    """
    Apply filter for age_to only (maximum age requirement).

    Business Logic: Book should be suitable for age_to and below.
    A book for ages 5-12 will match a user asking for age 10 and below.

    The filter includes books that:
    1. Have no lower age limit (suitable for all ages)
    2. Have a lower age limit that starts at or before the user's maximum age

    Args:
        query: SQLAlchemy query object
        age_to: Maximum user age
        book_model: SQLAlchemy Book model class

    Returns:
        Filtered SQLAlchemy query object

    Examples:
        >>> # User wants age 10 and below
        >>> # Book ages 5-12: ✅ Suitable (5 <= 10)
        >>> # Book ages 12-18: ❌ Not suitable (12 > 10)
        >>> # Book ages 0-8: ✅ Suitable (0 <= 10)
    """
    logger.debug(f"Applying age_to filter: {age_to} and below")

    return query.filter(
        or_(
            book_model.from_age.is_(None),  # No lower age limit
            book_model.from_age <= age_to,
        )
    )


@monitor_performance
def _apply_single_age_filter(query: Query, user_age: int, book_model: type[BookModelProtocol]) -> Query:
    """
    Apply filter for single age (exact age match).

    Business Logic: Book should be suitable for the user's exact age.
    A book for ages 8-12 will match a user age 10.

    The filter includes books that:
    1. Have no age restrictions (suitable for all ages)
    2. Have age ranges that include the user's exact age

    Args:
        query: SQLAlchemy query object
        user_age: User's exact age
        book_model: SQLAlchemy Book model class

    Returns:
        Filtered SQLAlchemy query object

    Examples:
        >>> # User is age 10
        >>> # Book ages 8-12: ✅ Suitable (8 <= 10 <= 12)
        >>> # Book ages 5-8: ❌ Not suitable (10 > 8)
        >>> # Book ages 12-18: ❌ Not suitable (10 < 12)
        >>> # Book ages 0+: ✅ Suitable (no restrictions)
    """
    logger.debug(f"Applying single age filter: {user_age}")

    return query.filter(
        or_(
            # Book has no age restrictions (suitable for all ages)
            and_(book_model.from_age.is_(None), book_model.to_age.is_(None)),
            # Book's age range includes the user's age
            and_(
                or_(book_model.from_age.is_(None), book_model.from_age <= user_age),
                or_(book_model.to_age.is_(None), book_model.to_age >= user_age),
            ),
        )
    )
