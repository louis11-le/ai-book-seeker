# LangSmith tracing: If LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY are set in the environment,
# all LangChain agent and tool calls will be traced and visible in your LangSmith dashboard.
"""
LangChain Orchestrator: Agent Integration

This module sets up the LangChain agent and integrates all modular tools for unified query processing.
It is designed for extensibility, onboarding, and auditability.
"""
import os
from typing import AsyncGenerator, Dict

from ai_book_seeker.api.schemas.chat import ChatResponse
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.prompts import get_system_prompt
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chat_models import init_chat_model
from langchain.memory import ConversationBufferMemory
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr

from .tools import get_all_tools

# TODO: Import and integrate advanced memory (e.g., MemorySaver) as needed

# Initialize module-level logger
logger = get_logger(__name__)


class LangChainOrchestrator:
    """
    Orchestrator for handling user queries using the LangChain agent and modular tools.
    Loads the system prompt from the versioned prompt file using get_system_prompt(),
    ensuring maintainability and auditability of prompt changes.
    Implements per-session memory using session_id for context isolation.

    IMPORTANT:
    - Output schema validation is enforced for all tools: every tool handler's output is validated against its
      Pydantic output schema before being returned to the agent/LLM.
    - This ensures all results are predictable, debuggable, and follow the architecture rules for solution quality
      and maintainability.
    - The FastAPI app instance is passed to all tool registrations for dependency injection (e.g., singleton FAQService).
    """

    def __init__(self, app):
        self.app = app
        # Aggregate all registered tools, passing the app instance
        self.tools = self._convert_tools(get_all_tools(app, "chat"))
        api_key = os.getenv("OPENAI_API_KEY")
        api_key = SecretStr(api_key) if isinstance(api_key, str) else api_key
        self.llm = init_chat_model(
            os.getenv("OPENAI_MODEL", "gpt-4o"),
            model_provider="openai",
            temperature=0.5,
        )

        # Load the system prompt from the versioned prompt file
        system_prompt = get_system_prompt()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        self.agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            self.prompt,
        )
        # Memory store: maps session_id to ConversationBufferMemory
        self._memory_store: Dict[str, ConversationBufferMemory] = {}
        # TODO: For production, use a persistent store (e.g., Redis) and ensure thread safety.
        # TODO: Integrate advanced memory (e.g., MemorySaver) for production

    def _get_memory(self, session_id: str) -> ConversationBufferMemory:
        """
        Retrieve or create a ConversationBufferMemory for the given session_id.
        """
        if session_id not in self._memory_store:
            self._memory_store[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output",  # Explicitly set to match agent's output key
            )

        return self._memory_store[session_id]

    def _convert_tools(self, tool_dicts) -> list:
        """
        Convert modular tool registrations to LangChain StructuredTool objects (async-compatible).
        Each tool dict must provide an async 'handler' function, input_schema, output_schema, name, and description.
        Input is validated, errors are logged, and real handler output is returned.

        NOTE: Output schema validation is enforced here—every tool's output is checked against its output_schema (Pydantic model).
        """
        tools = []

        def make_tool_func(handler, input_schema, output_schema, name):
            async def tool_func(**kwargs):
                try:
                    validated = input_schema(**kwargs)

                    result = await handler(validated)

                    if not isinstance(result, output_schema):
                        result = (
                            output_schema(**result) if isinstance(result, dict) else output_schema(text=str(result))
                        )

                    return result.dict()
                except Exception as e:
                    logger.error(f"tool_error: tool_name={name} error={e}", exc_info=True)
                    return output_schema(text=f"Error: {e}").dict()

            return tool_func

        for tool in tool_dicts:
            handler = tool["handler"]
            input_schema = tool["input_schema"]
            output_schema = tool["output_schema"]
            name = tool["name"]
            description = tool["description"]

            tool_func = make_tool_func(handler, input_schema, output_schema, name)
            structured_tool = StructuredTool.from_function(
                func=None,  # No sync implementation
                coroutine=tool_func,
                name=name,
                description=description,
                args_schema=input_schema,
            )
            tools.append(structured_tool)

        return tools

    async def process_query(self, query: str, session_id: str, interface: str = "chat") -> ChatResponse:
        """
        Process a user query using the LangChain agent.
        Args:
            query (str): The user's query.
            session_id (str): The session identifier.
            interface (str): The interface type (e.g., 'chat', 'voice').
        Returns:
            ChatResponse: The agent's response with output text.
        """
        try:
            memory = self._get_memory(session_id)
            # Get tools for this interface
            tools = self._convert_tools(get_all_tools(self.app, interface))
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=tools,
                memory=memory,
                verbose=True,
            )
            logger.info("query: %s", query)
            response = await agent_executor.ainvoke({"input": query})

            # --- Tool-agnostic output extraction (LangChain best practices) ---
            output_text = None
            if isinstance(response, dict):
                # Prefer 'output' key if present
                if "output" in response:
                    output_text = response["output"]
                # Next, try 'result' key
                elif "result" in response:
                    output_text = response["result"]
                # If only one key, use its value
                elif len(response) == 1:
                    output_text = list(response.values())[0]

            if output_text is None:
                # If response is a string, use it
                if isinstance(response, str):
                    output_text = response
                else:
                    output_text = str(response)

            return ChatResponse(output=output_text)
        except Exception as e:
            logger.error(f"agent_error: error={e}", exc_info=True)
            return ChatResponse(output="Sorry, there was an error processing your request. Please try again.")

    async def stream_query(
        self, query: str, session_id: str, interface: str = "chat"
    ) -> AsyncGenerator[ChatResponse, None]:
        """
        Stream agent responses for a user query using the LangChain agent.
        Args:
            query (str): The user's query.
            session_id (str): The session identifier.
            interface (str): The interface type (e.g., 'chat', 'voice').
        Yields:
            ChatResponse: Streaming agent response chunks with output text.
        """
        try:
            memory = self._get_memory(session_id)
            tools = self._convert_tools(get_all_tools(self.app, interface))
            agent_executor = AgentExecutor(
                agent=self.agent,
                tools=tools,
                memory=memory,
                verbose=True,
            )
            final_output = ""
            step_count = 0

            logger.info("=== STARTING STREAM QUERY ===")

            async for step in agent_executor.astream({"input": query}):
                step_count += 1
                logger.info(f"=== STEP {step_count} ===")

                output_text = None
                if isinstance(step, dict):
                    if "output" in step:
                        output_text = step["output"]
                    elif "result" in step:
                        output_text = step["result"]
                    elif len(step) == 1:
                        output_text = list(step.values())[0]

                if output_text is None:
                    if isinstance(step, str):
                        output_text = step
                    else:
                        output_text = str(step)

                # logger.debug(f"Step {step_count} output_text type: {type(output_text)}")
                # logger.debug(f"Step {step_count} output_text preview: {str(output_text)[:200]}...")

                # Only yield if this is a meaningful, user-facing answer (not intermediate/tool info)
                # Heuristic: Only yield if output_text is a plain string (not a dict or Python object string)
                if (
                    isinstance(output_text, str)
                    and not output_text.strip().startswith("{")
                    and output_text.strip() != ""
                ):
                    # logger.debug(f"Step {step_count}: FOUND USER-FACING OUTPUT")
                    final_output = output_text
                    # logger.debug(f"Step {step_count}: final_output set to: {final_output}")
                else:
                    # Log all intermediate/tool info
                    # logger.info(f"Step {step_count}: agent_intermediate_step: {output_text}")
                    pass

            logger.info("=== AGENT LOOP COMPLETED ===")
            logger.info(f"Total steps processed: {step_count}")
            logger.info(f"Final output length: {len(final_output)}")
            # logger.debug(f"Final output: {final_output}")

            # Production: yield the final output as a single chunk if available
            if final_output.strip():
                logger.info("Yielding final output as a single chunk.")
                yield ChatResponse(output=final_output)
            else:
                logger.info("=== NO FINAL OUTPUT, SENDING FALLBACK ===")
                yield ChatResponse(output="Sorry, no meaningful answer was generated.")
        except Exception as e:
            logger.error(f"agent_streaming_error: error={e}", exc_info=True)
            yield ChatResponse(output="Sorry, there was an error streaming your request. Please try again.")
