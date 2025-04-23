"""
Chat Parser Module for AI Book Seeker

This module handles natural language processing of user requests and generation of
responses using OpenAI's GPT-4. It implements chat message handling, session context
management, and tool-calling functionality for book recommendations.

Core components:
- Chat message models (ChatMessage, ChatRequest, ChatResponse)
- GPT-4 interaction logic
- Tool calling for book search functionality
- Session context management
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from db.connection import get_db
from logger import get_logger
from memory import SessionMemory
from prompts import get_system_prompt
from query import search_books_by_criteria
from tools import available_tools

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger("chat_parser")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get model from environment
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
# Get API parameters from environment with defaults
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "200"))

if not OPENAI_MODEL:
    logger.error("OPENAI_MODEL environment variable is required")
    raise ValueError("OPENAI_MODEL environment variable is required")


# System prompt - Load from versioned prompt file
SYSTEM_PROMPT = get_system_prompt()


# Models
class ChatMessage(BaseModel):
    """Model representing a single message in a chat conversation."""

    role: str
    content: Optional[str] = None
    name: Optional[str] = None


class ChatRequest(BaseModel):
    """Model representing a user's chat request."""

    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """Model representing the response to a chat request."""

    session_id: str
    response: str
    books: Optional[List[Dict[str, Any]]] = None


# Parsing functions
def create_chat_completion(messages: List[ChatMessage], session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a chat completion using OpenAI API with function calling support.

    Args:
        messages: List of chat messages to send to the API
        session_id: Optional session ID for including conversation context

    Returns:
        Dictionary containing the API response
    """
    try:
        # Add conversation context if a session ID is provided
        if session_id:
            context = SessionMemory.get_conversation_context(session_id)
            if context:
                # Insert context as the first user message
                context_msg = f"Here is the conversation history to provide context:\n\n{context}"
                context_message = ChatMessage(
                    role="system",
                    content=context_msg,
                )
                messages = [messages[0], context_message] + messages[1:]

        # Convert messages to the format expected by OpenAI API
        openai_messages = []
        for msg in messages:
            message_dict = {"role": msg.role}
            if msg.content is not None:
                message_dict["content"] = msg.content

            if msg.name is not None:
                message_dict["name"] = msg.name

            openai_messages.append(message_dict)

        # Call OpenAI API with function calling
        api_params = {
            "model": OPENAI_MODEL,
            "messages": openai_messages,
            "temperature": OPENAI_TEMPERATURE,
            "max_tokens": OPENAI_MAX_TOKENS,
        }

        # Add tools if available
        if available_tools:
            api_params["tools"] = available_tools  # type: ignore[assignment]
            api_params["tool_choice"] = "auto"
            logger.info("Using automatic tool selection")

        response = client.chat.completions.create(**api_params)  # type: ignore

        return response.model_dump()
    except Exception as e:
        logger.error(f"Error creating chat completion: {e}")
        raise


def process_chat_request(request: ChatRequest) -> ChatResponse:
    """
    Process a chat request and generate a response.

    Args:
        request: The chat request containing message and optional session ID

    Returns:
        A ChatResponse object with the assistant's response and book recommendations
    """
    # Initialize session_id at the function level for error handling
    session_id = request.session_id
    book_results = None
    assistant_response = ""

    try:
        # Manage session
        session_id = _ensure_session(session_id)

        # Create and process chat completion
        completion_result = _create_completion_with_context(request.message, session_id)

        # Extract response and handle tool calls
        assistant_response, book_results = _process_completion_result(completion_result)

        # Update session with this conversation turn
        SessionMemory.update_session(session_id, request.message, assistant_response)

        return ChatResponse(session_id=session_id, response=assistant_response, books=book_results)
    except Exception as e:
        return _handle_request_error(e, session_id)


def _ensure_session(session_id: Optional[str]) -> str:
    """Ensure a valid session ID exists, creating one if needed."""
    if not session_id:
        session_id = SessionMemory.create_session()
        logger.info(f"Created new session: {session_id}")
    else:
        logger.info(f"Using existing session: {session_id}")
    return session_id


def _create_completion_with_context(message: str, session_id: str) -> Dict[str, Any]:
    """Create a chat completion with the appropriate context."""
    system_message = ChatMessage(role="system", content=SYSTEM_PROMPT)
    user_message = ChatMessage(role="user", content=message)
    messages = [system_message, user_message]

    return create_chat_completion(messages, session_id)


def _process_completion_result(completion_result: Dict[str, Any]) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """
    Process the completion result to extract the assistant response and handle any tool calls.

    Args:
        completion_result: The result from the OpenAI API call

    Returns:
        A tuple of (assistant_response, book_results)
    """
    assistant_response = ""
    book_results = None

    if "choices" in completion_result and len(completion_result["choices"]) > 0:
        choice = completion_result["choices"][0]
        if "message" in choice and "content" in choice["message"] and choice["message"]["content"]:
            assistant_response = choice["message"]["content"]

        # Handle tool calls if present
        if "tool_calls" in choice["message"] and choice["message"]["tool_calls"]:
            for tool_call in choice["message"]["tool_calls"]:
                if tool_call["function"]["name"] == "search_books" and "arguments" in tool_call["function"]:
                    # Process book search tool call
                    assistant_response, book_results = _process_book_search(tool_call["function"]["arguments"])

    # If no valid response was generated, use a fallback
    if not assistant_response:
        assistant_response = "I'm sorry, I couldn't understand your request. Could you clarify?"

    return assistant_response, book_results


def _process_book_search(arguments_json: str) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """
    Process a book search tool call by parsing arguments and querying the database.

    Args:
        arguments_json: JSON string containing search arguments

    Returns:
        A tuple of (assistant_response, book_results)
    """
    assistant_response = ""
    book_results = None

    try:
        # Get the arguments provided by the AI
        args = json.loads(arguments_json)

        # Parse search parameters
        age = args.get("age")
        purpose = args.get("purpose")
        budget = args.get("budget")
        genre = args.get("genre")

        # Perform book search
        db = next(get_db())
        try:
            book_results = search_books_by_criteria(
                db=db,
                age=age,
                purpose=purpose,
                budget=budget,
                genre=genre,
            )
            logger.info(
                f"Found {len(book_results)} books matching criteria - age: {age}, purpose: {purpose}, budget: {budget}, genre: {genre}"
            )
        finally:
            db.close()

        # Generate response based on search results
        if book_results:
            assistant_response = _format_book_results(book_results)
        else:
            assistant_response = _get_no_results_response()
    except json.JSONDecodeError:
        logger.error(f"Error decoding tool call arguments: {arguments_json}")
        assistant_response = "I'm sorry, I encountered an error processing your book search. Please try again."

    return assistant_response, book_results


def _format_book_results(book_results: List[Dict[str, Any]]) -> str:
    """Format book results into a readable response."""
    response = "I found these books that match your criteria:\n\n"
    for book in book_results:
        response += f"- {book['title']} by {book['author']}: {book['description']}\n"
    return response


def _get_no_results_response() -> str:
    """Get a helpful response for when no books match the criteria."""
    return (
        "I couldn't find any books matching your criteria. "
        "This could be because:\n"
        "1. The age range you specified may be too specific\n"
        "2. The genre or theme might be uncommon\n"
        "3. The budget constraint may be too limiting\n\n"
        "Could you provide more details or adjust your preferences? "
        "For example, you might broaden the age range or try a different genre."
    )


def _handle_request_error(error: Exception, session_id: Optional[str] = None) -> ChatResponse:
    """Handle errors in request processing gracefully."""
    logger.error(f"Error processing chat request: {error}", exc_info=True)

    # Ensure we have a session ID for the response
    if not session_id:
        session_id = SessionMemory.create_session()
        logger.info(f"Created fallback session: {session_id}")

    return ChatResponse(
        session_id=session_id,
        response="I'm sorry, I encountered an error processing your request. Please try again.",
        books=None,
    )
