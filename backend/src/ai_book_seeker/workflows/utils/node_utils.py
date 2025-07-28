"""
Node utility functions for workflow orchestration.

Provides state validation, metrics tracking, and standardized Command creation
for workflow nodes. Error handling is provided by workflows/utils/error_handling.py
"""

from typing import Any, Dict, List, Optional, Union

from langgraph.types import Command

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.workflows.schemas import AgentState
from ai_book_seeker.workflows.utils.error_handling import create_error_message

logger = get_logger(__name__)


def validate_input_state(state: AgentState, node_name: str) -> Optional[Command]:
    """
    Validate input state before node processing.

    Args:
        state: Current workflow state to validate
        node_name: Name of the node for error context

    Returns:
        Optional[Command]: Error command if validation fails, None if valid
    """

    # Validate state exists
    logger.info(f"[{node_name}] Validating state")

    # Validate messages exist
    if not state.messages:
        logger.error(f"[{node_name}] No messages in state")
        error_msg = create_error_message(ValueError("No messages in state"), node_name, state.session_id)
        return Command(update={"messages": [error_msg]})

    # Validate session ID exists
    if not state.session_id:
        logger.error(f"[{node_name}] No session ID in state")
        error_msg = create_error_message(ValueError("No session ID in state"), node_name, state.session_id or "unknown")
        return Command(update={"messages": [error_msg]})

    # All validations passed - safe to log full state
    logger.info(f"[{node_name}] State is valid")
    logger.info(f"state: {state}")
    return None


def update_state_metrics(state: AgentState, metric_name: str) -> None:
    """
    Update performance metrics and access tracking for workflow state.

    Args:
        state: Current workflow state
        metric_name: Name of the metric to update
    """
    if not state.shared_data:
        return

    # Update access metrics
    state.shared_data.update_access_metrics()

    # Track performance metrics
    if metric_name not in state.shared_data.performance_metrics:
        state.shared_data.performance_metrics[metric_name] = {}

    state.shared_data.performance_metrics[metric_name].update(
        {
            "access_count": state.shared_data.access_count,
            "last_accessed": state.shared_data.last_accessed,
        }
    )


def create_command(
    messages: Union[List[Any], Any],
    state: AgentState,
    metric_name: Optional[str] = None,
    additional_updates: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    node_name: Optional[str] = None,
) -> Command:
    """
    Create Command with standardized state update pattern.

    Args:
        messages: Message(s) to add to state (single message or list)
        state: Current workflow state
        metric_name: Optional metric name for performance tracking
        additional_updates: Optional additional state updates
        trace_id: Trace ID for logging (optional)
        node_name: Node name for logging (optional)

    Returns:
        Command: Standardized command with state updates
    """
    # Convert single message to list for consistency
    if not isinstance(messages, list):
        messages = [messages]

    # Update metrics if provided
    if metric_name:
        update_state_metrics(state, metric_name)

    # Prepare update dictionary
    update_dict = {
        "messages": messages,
        "shared_data": state.shared_data,
    }

    # Add additional updates if provided
    if additional_updates:
        update_dict.update(additional_updates)

    # Create command without goto parameter (conditional edge routing)
    return Command(update=update_dict)
