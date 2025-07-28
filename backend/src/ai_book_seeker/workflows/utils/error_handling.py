"""
Error handling utilities for workflow nodes.

This module provides centralized error handling patterns to eliminate code duplication.
Follows context7 best practices for error handling and logging.
"""

from typing import Callable, Optional

from langchain_core.messages import SystemMessage
from langgraph.types import Command
from pydantic import ValidationError

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.schemas import AgentState

logger = get_logger(__name__)


def create_error_message(
    error: Exception,
    node_name: str,
    session_id: str,
    message_type: str = "error",
    content: Optional[str] = None,
) -> SystemMessage:
    """
    Create a standardized error message for workflow nodes.

    Args:
        error: The exception that occurred
        node_name: Name of the node where the error occurred
        session_id: Session ID for tracing
        message_type: Type of error message
        content: Custom error content (if None, uses str(error))

    Returns:
        SystemMessage: Standardized error message
    """

    error_content = content or f"{node_name} error: {str(error)}"
    return SystemMessage(
        content=error_content,
        additional_kwargs={
            "agent_name": node_name,
            "session_id": session_id,
            "message_type": message_type,
            "error_type": type(error).__name__,
        },
    )


def handle_node_error(
    error: Exception,
    node_name: str,
    state: AgentState,
    custom_content: Optional[str] = None,
) -> Command:
    """
    Handle errors in workflow nodes with standardized error handling.

    Args:
        error: The exception that occurred
        node_name: Name of the node where the error occurred
        state: Current workflow state
        custom_content: Custom error content

    Returns:
        Command: Error command with standardized error message
    """

    logger.error(f"[{node_name}][{state.session_id}] Error: {error}")
    error_msg = create_error_message(
        error=error,
        node_name=node_name,
        session_id=state.session_id,
        content=custom_content,
    )

    return Command(update={"messages": [error_msg]})


def handle_validation_error(
    error: ValidationError,
    node_name: str,
    state: AgentState,
) -> Command:
    """
    Handle validation errors specifically with detailed error information.

    Args:
        error: The validation error that occurred
        node_name: Name of the node where the error occurred
        state: Current workflow state

    Returns:
        Command: Error command with validation error details
    """

    logger.error(f"[{node_name}][{state.session_id}] Validation error: {error}")
    error_msg = create_error_message(
        error=error,
        node_name=node_name,
        session_id=state.session_id,
        message_type="validation_error",
        content=f"{node_name} validation error: {str(error)}",
    )

    return Command(update={"messages": [error_msg]})


def create_error_handler(
    node_name: str,
    custom_content: Optional[str] = None,
) -> Callable[[Exception, AgentState], Command]:
    """
    Create a reusable error handler for a specific node.

    Args:
        node_name: Name of the node
        custom_content: Custom error content template

    Returns:
        Callable: Error handler function
    """

    def error_handler(error: Exception, state: AgentState) -> Command:
        return handle_node_error(
            error=error,
            node_name=node_name,
            state=state,
            custom_content=custom_content,
        )

    return error_handler
