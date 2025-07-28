"""
Agent-related schemas for workflow management.

This module contains schemas for agent roles, insights, and results.
Follows industry best practices for agent schema design with optimized code reuse.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from ai_book_seeker.features.get_book_recommendation.schema import BookRecommendationOutputSchema
from ai_book_seeker.features.search_faq.schema import FAQOutputSchema


class AgentRole(BaseModel):
    """
    Defines the role and capabilities of an agent.

    Follows industry best practices for agent role definition:
    - Clear role identification
    - Explicit capability specification
    - Interface support declaration
    """

    name: str = Field(..., description="Unique agent identifier")
    role: str = Field(..., description="Human-readable role title")
    description: str = Field(..., description="Detailed role description")
    expertise: List[str] = Field(default_factory=list, description="Areas of expertise")
    available_tools: List[str] = Field(default_factory=list, description="Tools this agent can use")
    interface_support: List[str] = Field(default_factory=list, description="Supported interfaces (chat, voice)")


class AgentInsight(BaseModel):
    """
    Represents an agent's analysis and decision.

    Provides structured insight into agent reasoning and tool selection.
    """

    agent_name: str = Field(..., description="Name of the agent that generated this insight")
    role: str = Field(..., description="Agent's role for context")
    query_analysis: str = Field(..., description="Analysis of the user query")
    selected_tools: List[str] = Field(default_factory=list, description="Tools selected for this query")
    reasoning: str = Field(..., description="Reasoning behind tool selection")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in the analysis")


class AgentResults(BaseModel):
    """
    Container for agent execution results.

    Organizes results by tool type for easy access and validation.
    """

    faq: Optional[FAQOutputSchema] = Field(None, description="FAQ tool results")
    book_recommendation: Optional[BookRecommendationOutputSchema] = Field(
        None, description="Book recommendation results"
    )
    book_details: Optional[dict] = Field(None, description="Book details tool results")
