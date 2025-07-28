from ai_book_seeker.workflows.constants import BOOK_RECOMMENDATION_TOOL_NODE
from ai_book_seeker.workflows.prompts.agents import BaseAnalysisPromptTemplate
from ai_book_seeker.workflows.schemas import AgentRole

from .base import BaseAgent


class GeneralVoiceAgent(BaseAgent):
    """
    GeneralVoiceAgent handles voice interface queries using Book Recommendation tools.
    Enhanced with role-based behavior and LLM-based tool selection.
    """

    def __init__(self, llm=None):
        super().__init__(name="general_voice_agent", llm=llm)

    def _define_role(self) -> AgentRole:
        """
        Define the GeneralVoiceAgent's role and capabilities.

        Returns:
            AgentRole: The agent's role definition
        """
        return AgentRole(
            name="general_voice_agent",
            role="Voice Interface Specialist",
            description="Handles voice interface queries with focus on book recommendations",
            expertise=["Voice interaction", "Book recommendations", "Spoken language processing"],
            available_tools=[BOOK_RECOMMENDATION_TOOL_NODE],
            interface_support=["voice"],
        )

    def _create_analysis_prompt(self, query: str, router_context: str) -> str:
        """
        Create a specialized analysis prompt for GeneralVoiceAgent.

        Args:
            query: User query to analyze
            router_context: Router analysis context

        Returns:
            str: Specialized analysis prompt
        """
        specialized_guidance = f"""{BaseAnalysisPromptTemplate.get_general_guidance()}

{BaseAnalysisPromptTemplate.get_book_recommendation_guidance()}

{BaseAnalysisPromptTemplate.get_voice_interface_guidance()}

Specialized guidance for Voice Interface Specialist:
- If this is a multi-agent query, focus on YOUR expertise areas (voice interaction and book recommendations)"""

        return BaseAnalysisPromptTemplate.create_analysis_prompt(
            agent_role=self.role.role,
            expertise=self.role.expertise,
            available_tools=self.role.available_tools,
            query=query,
            router_context=router_context,
            specialized_guidance=specialized_guidance,
        )
