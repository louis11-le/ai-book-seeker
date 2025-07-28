"""
Base Analysis Prompt Template

This module provides the BaseAnalysisPromptTemplate class for creating standardized
analysis prompts used by agents in the workflow system.

The template follows the project's prompt management patterns and provides
utility methods to eliminate duplicate prompt creation code in agent implementations.

Key Features:
- Standardized prompt structure for consistent agent behavior
- Modular guidance system for different domains (FAQ, sales, voice, etc.)
- Confidence validation with centralized constants
- Multi-agent coordination support
- JSON output format for structured parsing

Usage:
    Agents combine multiple guidance sources to create specialized prompts:
    - GeneralAgent: general + FAQ + book recommendation guidance
    - GeneralVoiceAgent: general + book recommendation + voice guidance
    - SalesAgent: general + sales guidance

Constants:
    MIN_CONFIDENCE: Minimum confidence value (0.0)
    MAX_CONFIDENCE: Maximum confidence value (1.0)

Dependencies:
    - Used by all agent implementations for prompt creation
    - Constants used in validation across workflow system
    - Exported via workflows.prompts.agents package
"""

from typing import List

# Constants for validation and business logic
# These constants are used across the workflow system for confidence validation
MIN_CONFIDENCE = 0.0  # Minimum confidence value for agent analysis
MAX_CONFIDENCE = 1.0  # Maximum confidence value for agent analysis


class BaseAnalysisPromptTemplate:
    """
    Base template for creating analysis prompts with common patterns.

    This class provides a standardized approach to prompt engineering for agent
    analysis and tool selection. It eliminates code duplication by providing
    reusable components that agents can combine for their specific needs.

    Architecture:
    - Static methods for utility-style usage
    - Modular guidance system for different domains
    - Centralized constants for validation consistency
    - Structured JSON output format for reliable parsing

    Design Principles:
    - Single responsibility: Each method has a focused purpose
    - Composability: Agents can mix and match guidance sources
    - Consistency: Uniform prompt structure across all agents
    - Validation: Built-in confidence range enforcement

    Usage Pattern:
        Agents call create_analysis_prompt() with their specific parameters
        and combine multiple get_*_guidance() methods for specialized behavior.
    """

    @staticmethod
    def create_analysis_prompt(
        agent_role: str,
        expertise: List[str],
        available_tools: List[str],
        query: str,
        router_context: str,
        specialized_guidance: str,
    ) -> str:
        """
        Create a standardized analysis prompt with common structure.

        This method generates a comprehensive prompt that enables agents to:
        - Understand their role and available tools
        - Analyze user queries for intent and requirements
        - Select appropriate tools based on query content
        - Handle multi-agent and multi-tool scenarios
        - Provide structured JSON output for reliable parsing

        The prompt structure includes:
        - Agent role and expertise context
        - Available tools list
        - Router analysis context for multi-agent scenarios
        - Query analysis instructions
        - Confidence scoring requirements
        - Specialized guidance for domain-specific behavior

        Args:
            agent_role: The agent's role for context (e.g., "General Query Handler")
            expertise: Areas of expertise (e.g., ["FAQ handling", "Book recommendations"])
            available_tools: Tools this agent can use (e.g., ["faq_tool", "book_recommendation_tool"])
            query: User query to analyze for intent and tool requirements
            router_context: Router analysis context including multi-agent information
            specialized_guidance: Agent-specific guidance combining multiple guidance sources

        Returns:
            str: Standardized analysis prompt that produces structured JSON output with:
                - selected_tools: List of tools to use
                - reasoning: Explanation for tool selection
                - confidence: Confidence score between MIN_CONFIDENCE and MAX_CONFIDENCE
        """
        return f"""
You are a {agent_role} with expertise in: {', '.join(expertise)}

Available tools: {', '.join(available_tools)}

{router_context}

Analyze this user query: "{query}"

Determine:
1. Which tools are needed to handle this query
2. Your reasoning for tool selection
3. Your confidence level ({MIN_CONFIDENCE} to {MAX_CONFIDENCE})

If this is a multi-agent query (as indicated by router analysis), focus on YOUR expertise areas.
If this is a multi-purpose query but single agent, select ALL relevant tools.

{specialized_guidance}

Return JSON: {{
    "selected_tools": ["tool1", "tool2"],
    "reasoning": "explanation",
    "confidence": 0.85
}}

Note: Ensure your confidence score is between {MIN_CONFIDENCE} and {MAX_CONFIDENCE}.
"""

    @staticmethod
    def get_general_guidance() -> str:
        """
        Get general guidance for all agents.

        This guidance provides fundamental principles that apply to all agents
        regardless of their specialization. It focuses on query analysis,
        tool selection, and reasoning quality.

        Returns:
            str: General guidance text covering:
                - Query analysis best practices
                - Tool selection principles
                - Context consideration
                - Reasoning quality requirements
        """
        return """General guidance:
- Analyze the query carefully to understand user intent
- Select tools that best match the query requirements
- Consider the context from router analysis
- Provide clear reasoning for your tool selection"""

    @staticmethod
    def get_faq_guidance() -> str:
        """
        Get FAQ-specific guidance.

        This guidance helps agents identify and handle customer service
        and information-seeking queries that require FAQ tool usage.

        Returns:
            str: FAQ guidance text covering:
                - Customer service question identification
                - Policy and procedure inquiries
                - Store information requests
                - General information needs
        """
        return """FAQ guidance:
- Select FAQ tool for customer service questions
- Look for questions about policies, procedures, or general information
- Consider questions about store hours, returns, shipping, etc."""

    @staticmethod
    def get_book_recommendation_guidance() -> str:
        """
        Get book recommendation guidance.

        This guidance helps agents identify and handle reading-related
        queries that require book recommendation tool usage.

        Returns:
            str: Book recommendation guidance text covering:
                - Reading suggestion requests
                - Genre preference identification
                - Age-based recommendation needs
                - General recommendation queries
        """
        return """Book recommendation guidance:
- Select book recommendation tool for reading suggestions
- Look for requests for book recommendations, reading lists, or genre preferences
- Consider age-based, genre-based, or general recommendation requests"""

    @staticmethod
    def get_sales_guidance() -> str:
        """
        Get sales-specific guidance.

        This guidance helps agents identify and handle purchase-related
        queries that require sales tool usage.

        Returns:
            str: Sales guidance text covering:
                - Product inquiry identification
                - Purchase intent recognition
                - Pricing and availability questions
                - Order-related queries
        """
        return """Sales guidance:
- Select sales tools for purchase-related queries
- Look for product inquiries, pricing questions, or purchase intent
- Consider questions about specific books, availability, or ordering"""

    @staticmethod
    def get_voice_interface_guidance() -> str:
        """
        Get voice interface guidance.

        This guidance helps agents optimize their responses for voice
        interface interactions, considering spoken language patterns
        and conversational flow.

        Returns:
            str: Voice interface guidance text covering:
                - Spoken language optimization
                - Conversational flow considerations
                - Voice output suitability
                - Natural language patterns
        """
        return """Voice interface guidance:
- Optimize for spoken language patterns
- Consider conversational flow and natural language
- Focus on clear, concise responses suitable for voice output"""
