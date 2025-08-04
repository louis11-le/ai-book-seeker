from langchain_core.language_models import BaseLanguageModel

from ai_book_seeker.workflows.constants import BOOK_RECOMMENDATION_TOOL_NODE, FAQ_TOOL_NODE
from ai_book_seeker.workflows.prompts.agents import BaseAnalysisPromptTemplate
from ai_book_seeker.workflows.schemas import AgentRole

from .base import BaseAgent


class GeneralAgent(BaseAgent):
    """
    GeneralAgent handles general user queries using FAQ and Book Recommendation tools.

    This agent is designed for chat interface queries and specializes in:
    - FAQ handling and customer service questions
    - Book recommendations based on user criteria
    - Multi-tool parallel execution for complex queries

    Implements the Template Method pattern from BaseAgent with:
    - Role-based behavior definition
    - LLM-powered query analysis and tool selection
    - Specialized prompt engineering for general queries

    Available Tools:
    - FAQ Tool: For customer service and policy questions
    - Book Recommendation Tool: For personalized book suggestions

    Interface Support: Chat only (voice queries handled by GeneralVoiceAgent)
    """

    def __init__(self, llm: BaseLanguageModel) -> None:
        """
        Initialize the GeneralAgent with required language model.

        Args:
            llm: Language model for query analysis and tool selection (required)
        """
        super().__init__(name="general_agent", llm=llm)

    def _define_role(self) -> AgentRole:
        """
        Define the GeneralAgent's role and capabilities.

        Returns:
            AgentRole: The agent's role definition with:
                - name: "general_agent"
                - role: "General Query Handler"
                - expertise: FAQ handling, book recommendations, customer support
                - available_tools: FAQ and book recommendation tools
                - interface_support: Chat interface only
        """
        return AgentRole(
            name="general_agent",
            role="General Query Handler",
            description="Handles general user queries including FAQs and book recommendations",
            expertise=["FAQ handling", "Book recommendations", "General customer support"],
            available_tools=[FAQ_TOOL_NODE, BOOK_RECOMMENDATION_TOOL_NODE],
            interface_support=["chat"],
        )

    def _create_analysis_prompt(self, query: str, router_context: str) -> str:
        """
        Create a specialized analysis prompt for GeneralAgent.

        This method combines multiple guidance sources to create a comprehensive
        prompt that enables the agent to:
        - Analyze queries for FAQ and book recommendation elements
        - Select appropriate tools based on query content
        - Handle multi-tool scenarios when both FAQ and recommendations are needed
        - Focus on expertise areas in multi-agent scenarios

        Args:
            query: User query to analyze for intent and tool requirements
            router_context: Router analysis context including multi-agent information

        Returns:
            str: Specialized analysis prompt combining general, FAQ, and book
                 recommendation guidance with agent-specific instructions
        """
        specialized_guidance = f"""{BaseAnalysisPromptTemplate.get_general_guidance()}

{BaseAnalysisPromptTemplate.get_faq_guidance()}

{BaseAnalysisPromptTemplate.get_book_recommendation_guidance()}

Specialized guidance for General Query Handler:
- If query contains both FAQ and book recommendation elements, select BOTH tools for parallel execution
- If this is a multi-agent query, focus on YOUR expertise areas (FAQ and book recommendations)"""

        return BaseAnalysisPromptTemplate.create_analysis_prompt(
            agent_role=self.role.role,
            expertise=self.role.expertise,
            available_tools=self.role.available_tools,
            query=query,
            router_context=router_context,
            specialized_guidance=specialized_guidance,
        )
