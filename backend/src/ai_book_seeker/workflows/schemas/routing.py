"""
Routing schemas for workflow orchestration.

This module contains schemas for routing analysis and workflow state management.
Follows industry best practices for routing schema design with comprehensive validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


# Constants for validation and configuration
class RoutingConstants:
    """Constants for routing validation and configuration."""

    # Confidence score bounds
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 1.0
    DEFAULT_CONFIDENCE = 0.5

    # Reasoning constraints
    MAX_REASONING_WORDS = 50

    # Node name patterns
    VALID_NODE_PATTERNS = [
        "general_agent",
        "general_voice_agent",
        "sales_agent",
        "agent_coordinator",
        "parameter_extraction",
        "parallel_tool_execution",
        "merge_tools",
        "format_response",
        "error",
    ]

    # Agent name patterns
    VALID_AGENT_PATTERNS = ["general_agent", "general_voice_agent"]  # "sales_agent" temporarily disabled


class RoutingAnalysis(BaseModel):
    """
    Enhanced routing analysis with structured categorization.

    Provides comprehensive routing decisions for multi-agent and multi-purpose queries.
    Follows industry best practices for routing analysis.

    Attributes:
        next_node: Immediate next node to route to in the workflow
        participating_agents: List of agents for parallel orchestration
        is_multi_purpose: Whether the query has multiple purposes
        is_multi_agent: Whether the query requires multiple agents
        reasoning: Human-readable explanation of routing decision
        confidence: Confidence score for the routing decision (0.0-1.0)

    Example:
        ```python
        analysis = RoutingAnalysis(
            next_node="agent_coordinator",
            participating_agents=["general_agent", "sales_agent"],
            is_multi_purpose=True,
            is_multi_agent=True,
            reasoning="Multi-agent query detected",
            confidence=0.95
        )
        ```
    """

    next_node: str = Field(
        ...,
        min_length=1,
        description="Immediate next node to route to in the workflow (e.g., 'general_agent', 'sales_agent', 'agent_coordinator')",
    )
    participating_agents: List[str] = Field(
        default_factory=list,
        description="List of agents that should participate in parallel orchestration for multi-agent queries",
    )
    is_multi_purpose: bool = Field(
        default=False, description="Whether the query has multiple purposes requiring different tools"
    )
    is_multi_agent: bool = Field(
        default=False, description="Whether the query requires multiple agents for parallel processing"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Human-readable explanation of the routing decision (max 30 words)"
    )
    confidence: float = Field(
        default=RoutingConstants.DEFAULT_CONFIDENCE,
        ge=RoutingConstants.MIN_CONFIDENCE,
        le=RoutingConstants.MAX_CONFIDENCE,
        description="Confidence score for the routing decision (0.0-1.0)",
    )

    @field_validator("next_node")
    @classmethod
    def validate_next_node(cls, v: str) -> str:
        """Validate that next_node is a valid workflow node."""
        # Direct validation
        if not v or not v.strip():
            raise ValueError("next_node cannot be empty")

        cleaned_value = v.strip()

        # Validate pattern without failing (just log warning)
        if cleaned_value not in RoutingConstants.VALID_NODE_PATTERNS:
            logger.warning(
                f"Unknown node pattern: {cleaned_value}. Valid patterns: {RoutingConstants.VALID_NODE_PATTERNS}"
            )

        return cleaned_value

    @field_validator("participating_agents")
    @classmethod
    def validate_participating_agents(cls, v: List[str]) -> List[str]:
        """Validate that participating_agents contains valid agent names."""

        validated_agents = []
        for agent in v:
            if not agent or not agent.strip():
                continue  # Skip empty agents

            agent = agent.strip()
            if agent not in RoutingConstants.VALID_AGENT_PATTERNS:
                logger.warning(
                    f"Unknown agent pattern: {agent}. Valid patterns: {RoutingConstants.VALID_AGENT_PATTERNS}"
                )

            validated_agents.append(agent)

        return validated_agents

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning(cls, v: Optional[str]) -> Optional[str]:
        """Validate that reasoning is properly formatted and within word limit."""

        if v is None:
            return v

        if not isinstance(v, str):
            raise ValueError("reasoning must be a string")

        cleaned = v.strip()
        if not cleaned:
            return None

        # Check word count (max 30 words)
        words = cleaned.split()
        if len(words) > RoutingConstants.MAX_REASONING_WORDS:
            logger.warning(
                f"Reasoning exceeds {RoutingConstants.MAX_REASONING_WORDS} words ({len(words)} words), truncating"
            )
            truncated_words = words[: RoutingConstants.MAX_REASONING_WORDS]
            return " ".join(truncated_words) + "..."

        return cleaned

    def is_valid_for_execution(self) -> bool:
        """
        Check if the routing analysis is valid for workflow execution.

        Returns:
            bool: True if the analysis can be used for routing decisions
        """
        return (
            bool(self.next_node)
            and self.confidence >= RoutingConstants.MIN_CONFIDENCE
            and self.confidence <= RoutingConstants.MAX_CONFIDENCE
        )

    def get_agent_count(self) -> int:
        """
        Get the number of participating agents.

        Returns:
            int: Number of agents that will participate in processing
        """
        return len(self.participating_agents) if self.participating_agents else 0

    def requires_coordination(self) -> bool:
        """
        Check if this routing decision requires agent coordination.

        Returns:
            bool: True if multiple agents need to be coordinated
        """
        return self.is_multi_agent and self.get_agent_count() > 1

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return (
            f"RoutingAnalysis("
            f"next_node='{self.next_node}', "
            f"participating_agents={self.participating_agents}, "
            f"multi_purpose={self.is_multi_purpose}, "
            f"multi_agent={self.is_multi_agent}, "
            f"confidence={self.confidence:.2f}"
            f")"
        )
