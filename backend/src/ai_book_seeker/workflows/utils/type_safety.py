"""
Type safety utilities for LangGraph workflow state management.

This module provides type safety decorators for merge operations.
"""

import inspect
from typing import Callable, TypeVar

from ..schemas.agents import AgentResults
from ..schemas.state import SharedData

# Type variables for generic functions
F = TypeVar("F", bound=Callable)

# Type aliases for common patterns
StateObject = AgentResults | SharedData

# =============================================================================
# TYPE VALIDATION DECORATORS
# =============================================================================


def validate_merge_function(func: F) -> F:
    """
    Decorator to validate merge function parameters and return type.

    Args:
        func: The merge function to validate
    """

    @inspect.signature(func)
    def wrapper(left: StateObject, right: StateObject) -> StateObject:
        # Validate input parameters
        if not isinstance(left, (AgentResults, SharedData)):
            raise TypeError(f"Left parameter must be AgentResults or SharedData, got {type(left).__name__}")

        if not isinstance(right, (AgentResults, SharedData)):
            raise TypeError(f"Right parameter must be AgentResults or SharedData, got {type(right).__name__}")

        # Ensure both parameters are of the same type
        if not isinstance(left, type(right)) and not isinstance(right, type(left)):
            raise TypeError(
                f"Both parameters must be of the same type, got {type(left).__name__} and {type(right).__name__}"
            )

        result = func(left, right)

        # Validate return type matches input type
        expected_type = type(left)
        if not isinstance(result, expected_type):
            raise TypeError(f"Return value must be {expected_type.__name__}, got {type(result).__name__}")

        return result

    return wrapper


# =============================================================================
# TYPE VALIDATION DECORATORS
# =============================================================================


def ensure_type_safety(func: F) -> F:
    """
    Decorator to ensure type safety for merge functions.

    This decorator validates input types and return types at runtime.

    Args:
        func: The function to make type-safe
    """

    @validate_merge_function
    @inspect.signature(func)
    def wrapper(left: StateObject, right: StateObject) -> StateObject:
        return func(left, right)

    return wrapper
