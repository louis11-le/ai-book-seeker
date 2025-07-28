"""
Workflow schemas for agent orchestration and state management.

This module provides Pydantic models for workflow state, agent roles, and communication.
Follows industry best practices for schema design and validation.
"""

from .agents import AgentInsight, AgentResults, AgentRole
from .intents import BookRecommendationRequest, FAQRequest, ProductInquiry, SalesRequest
from .routing import RoutingAnalysis
from .state import AgentState, SharedData, get_state_manager

__all__ = [
    "AgentInsight",
    "AgentResults",
    "AgentRole",
    "BookRecommendationRequest",
    "FAQRequest",
    "ProductInquiry",
    "SalesRequest",
    "RoutingAnalysis",
    "AgentState",
    "SharedData",
    "get_state_manager",
]
