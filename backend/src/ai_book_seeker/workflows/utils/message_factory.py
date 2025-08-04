"""
Message factory utilities for workflow nodes.

This module provides centralized message creation patterns to eliminate code duplication.
Follows context7 best practices for message creation and consistency.
"""

from typing import Any, Dict, Optional

from langchain_core.messages import AIMessage, SystemMessage

from ai_book_seeker.workflows.constants import AGENT_COORDINATOR_NODE, PARAMETER_EXTRACTION_NODE, ROUTER_NODE


def _create_base_kwargs(
    name: str,
    session_id: str,
    message_type: str,
    name_key: str = "agent_name",
    additional_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create standardized base keyword arguments for message creation.

    This helper function eliminates code duplication across message creation functions
    by centralizing the common base_kwargs pattern.

    Args:
        name: Name of the agent/tool/node creating the message
        session_id: Session ID for tracing
        message_type: Type of message
        name_key: Key for the name field ("agent_name" or "tool_name")
        additional_kwargs: Additional keyword arguments to merge

    Returns:
        Dict[str, Any]: Standardized base keyword arguments
    """
    base_kwargs = {
        name_key: name,
        "session_id": session_id,
        "message_type": message_type,
    }

    if additional_kwargs:
        base_kwargs.update(additional_kwargs)

    return base_kwargs


def create_system_message(
    content: str,
    node_name: str,
    session_id: str,
    message_type: str = "system",
    additional_kwargs: Optional[Dict[str, Any]] = None,
) -> SystemMessage:
    """
    Create a standardized system message for workflow nodes.

    Args:
        content: Message content
        node_name: Name of the node creating the message
        session_id: Session ID for tracing
        message_type: Type of message
        additional_kwargs: Additional keyword arguments

    Returns:
        SystemMessage: Standardized system message
    """
    base_kwargs = _create_base_kwargs(
        name=node_name,
        session_id=session_id,
        message_type=message_type,
        name_key="agent_name",
        additional_kwargs=additional_kwargs,
    )

    return SystemMessage(
        content=content,
        additional_kwargs=base_kwargs,
    )


def create_ai_message(
    content: str,
    node_name: str,
    session_id: str,
    message_type: str = "ai",
    additional_kwargs: Optional[Dict[str, Any]] = None,
) -> AIMessage:
    """
    Create a standardized AI message for workflow nodes.

    Args:
        content: Message content
        node_name: Name of the node creating the message
        session_id: Session ID for tracing
        message_type: Type of message
        additional_kwargs: Additional keyword arguments

    Returns:
        AIMessage: Standardized AI message
    """
    base_kwargs = _create_base_kwargs(
        name=node_name,
        session_id=session_id,
        message_type=message_type,
        name_key="agent_name",
        additional_kwargs=additional_kwargs,
    )

    return AIMessage(
        content=content,
        additional_kwargs=base_kwargs,
    )


def create_tool_message(
    content: str,
    tool_name: str,
    session_id: str,
    message_type: str = "tool_execution",
    additional_kwargs: Optional[Dict[str, Any]] = None,
) -> AIMessage:
    """
    Create a standardized tool execution message.

    Args:
        content: Message content
        tool_name: Name of the tool
        session_id: Session ID for tracing
        message_type: Type of message
        additional_kwargs: Additional keyword arguments

    Returns:
        AIMessage: Standardized tool message
    """
    base_kwargs = _create_base_kwargs(
        name=tool_name,
        session_id=session_id,
        message_type=message_type,
        name_key="tool_name",
        additional_kwargs=additional_kwargs,
    )

    return AIMessage(
        content=content,
        additional_kwargs=base_kwargs,
    )


def create_routing_message(
    next_node: str,
    participating_agents: list,
    confidence: float,
    session_id: str,
) -> SystemMessage:
    """
    Create a standardized routing decision message.

    Args:
        next_node: Next node to route to
        participating_agents: List of participating agents
        confidence: Routing confidence
        session_id: Session ID for tracing

    Returns:
        SystemMessage: Standardized routing message
    """
    return create_system_message(
        content=f"Query analyzed. Routing to {next_node}",
        node_name=ROUTER_NODE,
        session_id=session_id,
        message_type="routing_decision",
        additional_kwargs={
            "next_node": next_node,
            "participating_agents": participating_agents,
            "confidence": confidence,
        },
    )


def create_coordination_message(
    participating_agents: list,
    session_id: str,
) -> SystemMessage:
    """
    Create a standardized agent coordination message.

    Args:
        participating_agents: List of participating agents
        session_id: Session ID for tracing

    Returns:
        SystemMessage: Standardized coordination message
    """
    return create_system_message(
        content=f"Coordinating {len(participating_agents)} agents for multi-agent query",
        node_name=AGENT_COORDINATOR_NODE,
        session_id=session_id,
        message_type="agent_coordination_start",
        additional_kwargs={
            "agents_count": len(participating_agents),
            "participating_agents": participating_agents,
            "performance_optimized": False,
        },
    )


def create_parameter_message(
    extracted_parameters: dict,
    session_id: str,
) -> SystemMessage:
    """
    Create a standardized parameter extraction message.

    Args:
        extracted_parameters: Extracted parameters
        session_id: Session ID for tracing

    Returns:
        SystemMessage: Standardized parameter message
    """
    return create_system_message(
        content=f"Parameters extracted: {len(extracted_parameters)} parameters found",
        node_name=PARAMETER_EXTRACTION_NODE,
        session_id=session_id,
        message_type="parameter_extraction_complete",
        additional_kwargs={
            "parameters_count": len(extracted_parameters),
            "extracted_parameters": extracted_parameters,
        },
    )
