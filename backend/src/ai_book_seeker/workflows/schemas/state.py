"""
State management schemas and utilities for workflow orchestration.
"""

import time
from typing import Annotated, Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from ai_book_seeker.core.logging import get_logger

from .agents import AgentInsight, AgentResults, AgentRole
from .routing import RoutingAnalysis

logger = get_logger(__name__)


class TimestampedModel(BaseModel):
    """Base class for models that track creation and access timestamps."""

    created_at: Optional[float] = Field(default=None, description="Creation timestamp")
    last_accessed: Optional[float] = Field(default=None, description="Last access timestamp")
    access_count: int = Field(default=0, description="Number of accesses")

    model_config = {"validate_assignment": True, "extra": "forbid"}

    def update_access_metrics(self) -> None:
        """Update access metrics for performance tracking."""
        self.last_accessed = time.time()
        self.access_count += 1


class PerformanceTrackedModel(BaseModel):
    """Base class for models that track performance metrics."""

    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance tracking data")

    model_config = {"validate_assignment": True, "extra": "forbid"}


class SharedData(TimestampedModel, PerformanceTrackedModel):
    """Shared data across the workflow."""

    extracted_parameters: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    agent_insights: List[AgentInsight] = Field(default_factory=list, description="Agent analysis insights")
    current_agent_role: Optional[AgentRole] = None
    selected_tools_for_parallel: Optional[List[str]] = None
    participating_agents_for_parallel: Optional[List[str]] = None
    routing_analysis: Optional[RoutingAnalysis] = None


def merge_agent_results(left: AgentResults, right: AgentResults) -> AgentResults:
    """Merge two AgentResults objects for concurrent updates in LangGraph."""
    try:
        merged = left.model_copy()

        if right.faq is not None:
            merged.faq = right.faq

        if right.book_recommendation is not None:
            merged.book_recommendation = right.book_recommendation

        if right.book_details is not None:
            merged.book_details = right.book_details

        return merged
    except Exception:
        return right


def merge_shared_data(left: SharedData, right: SharedData) -> SharedData:
    """Merge SharedData objects for concurrent updates in LangGraph."""
    try:
        merged = left.model_copy()

        if right.agent_insights:
            # Deduplication logic: only add insights that don't already exist from the same agent
            existing_agent_names = {insight.agent_name for insight in merged.agent_insights}
            new_insights = []
            for insight in right.agent_insights:
                if insight.agent_name not in existing_agent_names:
                    new_insights.append(insight)
                    logger.debug(f"Adding new insight from agent: {insight.agent_name}")
                else:
                    logger.debug(f"Skipping duplicate insight from agent: {insight.agent_name}")

            if new_insights:
                merged.agent_insights.extend(new_insights)
                logger.info(
                    f"Added {len(new_insights)} new insights, skipped {len(right.agent_insights) - len(new_insights)} duplicates"
                )
            else:
                logger.info(f"All {len(right.agent_insights)} insights were duplicates, none added")

        if right.performance_metrics:
            merged.performance_metrics.update(right.performance_metrics)

        if right.routing_analysis is not None:
            merged.routing_analysis = right.routing_analysis

        if right.extracted_parameters is not None:
            merged.extracted_parameters = right.extracted_parameters

        if right.correlation_id is not None:
            merged.correlation_id = right.correlation_id

        if right.current_agent_role is not None:
            merged.current_agent_role = right.current_agent_role

        if right.selected_tools_for_parallel is not None:
            merged.selected_tools_for_parallel = right.selected_tools_for_parallel

        if right.participating_agents_for_parallel is not None:
            merged.participating_agents_for_parallel = right.participating_agents_for_parallel

        merged.access_count = left.access_count + right.access_count
        merged.last_accessed = max(left.last_accessed or 0, right.last_accessed or 0)

        return merged
    except Exception:
        return right


class AgentState(TimestampedModel, PerformanceTrackedModel):
    """State for the LangGraph workflow."""

    session_id: str
    interface: str
    current_agent: str
    messages: Annotated[List[BaseMessage], add_messages]
    shared_data: Annotated[SharedData, merge_shared_data]
    agent_results: Annotated[AgentResults, merge_agent_results]
    execution_start_time: Optional[float] = Field(default=None, description="Workflow execution start time")

    def __init__(self, **data):
        super().__init__(**data)
        current_time = time.time()
        self.created_at = current_time
        self.execution_start_time = current_time

    def validate_state_consistency(self) -> bool:
        """Validate state consistency and return True if valid."""
        return (
            bool(self.session_id and self.session_id.strip())
            and self.interface in {"chat", "voice"}
            and bool(self.current_agent and self.current_agent.strip())
            and isinstance(self.messages, list)
            and isinstance(self.shared_data, SharedData)
            and isinstance(self.agent_results, AgentResults)
        )

    def get_execution_time(self) -> float:
        """Get current execution time in seconds."""
        return time.time() - self.execution_start_time if self.execution_start_time else 0.0

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state for monitoring and debugging."""
        return {
            "session_id": self.session_id,
            "interface": self.interface,
            "current_agent": self.current_agent,
            "messages_count": len(self.messages),
            "execution_time": self.get_execution_time(),
            "shared_data_access_count": self.shared_data.access_count,
            "agent_insights_count": len(self.shared_data.agent_insights),
            "has_routing_analysis": self.shared_data.routing_analysis is not None,
            "has_extracted_parameters": self.shared_data.extracted_parameters is not None,
        }


class StateManager:
    """Utility class for efficient state management operations."""

    def __init__(self):
        self.state_cache = {}

    def create_initial_state(
        self, session_id: str, interface: str, message: str, correlation_id: Optional[str] = None
    ) -> AgentState:
        """Create an optimized initial state with proper initialization."""
        shared_data = SharedData(
            correlation_id=correlation_id,
            created_at=time.time(),
        )

        state = AgentState(
            session_id=session_id,
            interface=interface,
            current_agent="router",
            messages=[HumanMessage(content=message)],
            shared_data=shared_data,
            agent_results=AgentResults(),
        )

        if not state.validate_state_consistency():
            raise ValueError(f"State validation failed for session {session_id} during initialization")

        self.state_cache[session_id] = state
        return state

    def get_state_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get state summary for monitoring and debugging."""
        state = self.state_cache.get(session_id)
        return state.get_state_summary() if state else None

    def cleanup_old_states(self, max_age_seconds: int = 3600) -> int:
        """Clean up old states to free memory."""
        current_time = time.time()
        sessions_to_remove = [
            session_id
            for session_id, state in self.state_cache.items()
            if state.created_at and (current_time - state.created_at) > max_age_seconds
        ]

        for session_id in sessions_to_remove:
            del self.state_cache[session_id]

        return len(sessions_to_remove)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for state management."""
        states = list(self.state_cache.values())
        return {
            "cached_states_count": len(self.state_cache),
            "total_sessions_processed": len(states),
            "average_access_count": sum(state.shared_data.access_count for state in states) / max(len(states), 1),
            "memory_optimization_enabled": True,
        }


_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Get the global state manager instance."""
    return _state_manager
