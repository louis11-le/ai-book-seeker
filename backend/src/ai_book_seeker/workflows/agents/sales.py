"""
SalesAgent for workflow orchestration.

This module provides the SalesAgent class with explicit implementation
for handling sales-related queries including purchases, orders, and product details.
"""

from langchain_core.language_models import BaseLanguageModel

from ai_book_seeker.workflows.constants import BOOK_DETAILS_TOOL_NODE
from ai_book_seeker.workflows.prompts.agents import BaseAnalysisPromptTemplate
from ai_book_seeker.workflows.schemas import AgentRole

from .base import BaseAgent


class SalesAgent(BaseAgent):
    """
    SalesAgent handles sales-related queries using Book Details tools.
    Enhanced with role-based behavior and LLM-based tool selection.
    """

    def __init__(self, llm: BaseLanguageModel) -> None:
        """
        Initialize the SalesAgent with required language model.

        Args:
            llm: Language model for query analysis and tool selection (required)
        """
        super().__init__(name="sales_agent", llm=llm)

    def _define_role(self) -> AgentRole:
        """
        Define the SalesAgent's role and capabilities.

        Returns:
            AgentRole: The agent's role definition
        """
        return AgentRole(
            name="sales_agent",
            role="Sales Specialist",
            description="Handles sales-related queries including product details and purchase assistance",
            expertise=["Sales", "Order processing", "Product information", "Pricing"],
            available_tools=[BOOK_DETAILS_TOOL_NODE],
            interface_support=["chat", "voice"],
        )

    def _create_analysis_prompt(self, query: str, router_context: str) -> str:
        """
        Create a specialized analysis prompt for SalesAgent.

        Args:
            query: User query to analyze
            router_context: Router analysis context

        Returns:
            str: Specialized analysis prompt
        """
        specialized_guidance = f"""{BaseAnalysisPromptTemplate.get_general_guidance()}

{BaseAnalysisPromptTemplate.get_sales_guidance()}

Specialized guidance for Sales Specialist:
- Focus on sales-related aspects: ordering, purchasing, product details, pricing
- Consider the commercial intent of the query
- Handle product information, availability, and purchase-related questions"""

        return BaseAnalysisPromptTemplate.create_analysis_prompt(
            agent_role=self.role.role,
            expertise=self.role.expertise,
            available_tools=self.role.available_tools,
            query=query,
            router_context=router_context,
            specialized_guidance=specialized_guidance,
        )
