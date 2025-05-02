"""
Session Memory Manager for AI Book Seeker

This module handles conversation history management, persistence, and retrieval.
It provides functionality for creating, retrieving, updating, and deleting chat sessions,
as well as compressing conversation history to maintain context within token limits.

The SessionMemory class uses Redis for storing session data with appropriate TTL (time-to-live)
settings and implements conversation context compression using OpenAI's GPT-4.
"""

import json
import time
import uuid
from typing import Any, Dict, Optional

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

from ai_book_seeker.core.config import OPENAI_API_KEY, OPENAI_MODEL, REDIS_EXPIRE_SECONDS
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.connection import redis_client

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger("memory")

# Constants
MAX_TURNS_TO_STORE = 10
MAX_TOKENS_FOR_CONTEXT = 4000  # Limit to avoid hitting token limits
ENCODING = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class SessionMemory:
    """Handles conversation history management and compression"""

    @staticmethod
    def get_session_key(session_id: str) -> str:
        """Get Redis key for a session"""
        return f"session:{session_id}"

    @staticmethod
    def create_session() -> str:
        """Create a new session and return the session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "recent_turns": [],
            "compressed_summary": "",
            "expires_at": int(time.time()) + REDIS_EXPIRE_SECONDS,
        }

        redis_client.set(
            SessionMemory.get_session_key(session_id),
            json.dumps(session_data),
            ex=REDIS_EXPIRE_SECONDS,
        )

        logger.info(f"Created new session: {session_id}")
        return session_id

    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        try:
            session_key = SessionMemory.get_session_key(session_id)
            session_data = redis_client.get(session_key)
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return None

            # Ensure session_data is a string or bytes for json.loads
            if isinstance(session_data, bytes):
                session_data_str = session_data.decode("utf-8")
            else:
                # Convert to string if it's another type
                session_data_str = str(session_data)

            return json.loads(session_data_str)
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    @staticmethod
    def update_session(session_id: str, user_message: str, ai_response: str) -> None:
        """Update session with new message turn"""
        session_data = SessionMemory.get_session(session_id)
        if not session_data:
            # Session doesn't exist, create a new one
            logger.warning(f"Session {session_id} not found, creating new session")
            session_id = SessionMemory.create_session()
            session_data = SessionMemory.get_session(session_id)
            if not session_data:
                logger.error("Failed to create new session")
                return

        # Add new turn
        new_turn = {
            "user": user_message,
            "ai": ai_response,
            "timestamp": int(time.time()),
        }

        session_data["recent_turns"].append(new_turn)

        # If we're exceeding max turns, compress older ones
        if len(session_data["recent_turns"]) > MAX_TURNS_TO_STORE:
            # Keep the most recent MAX_TURNS_TO_STORE - 1 turns
            turns_to_compress = session_data["recent_turns"][: -MAX_TURNS_TO_STORE + 1]
            session_data["recent_turns"] = session_data["recent_turns"][-MAX_TURNS_TO_STORE + 1 :]

            # Compress older turns
            older_context = ""
            for turn in turns_to_compress:
                older_context += f"User: {turn['user']}\nAI: {turn['ai']}\n\n"

            # If there's already a summary, include it in compression
            if session_data["compressed_summary"]:
                older_context = session_data["compressed_summary"] + "\n\n" + older_context

            # Generate a new compressed summary
            session_data["compressed_summary"] = SessionMemory.compress_history(older_context)

        # Reset expiration
        session_data["expires_at"] = int(time.time()) + REDIS_EXPIRE_SECONDS

        # Save updated session
        try:
            redis_client.set(
                SessionMemory.get_session_key(session_id),
                json.dumps(session_data),
                ex=REDIS_EXPIRE_SECONDS,
            )
            logger.debug(f"Updated session: {session_id}")
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")

    @staticmethod
    def compress_history(conversation_history: str) -> str:
        """Compress conversation history using GPT-4"""
        try:
            system_message = (
                "You are a helpful assistant that summarizes conversations. "
                "Create a concise summary of the key points, user preferences, "
                "and important information mentioned in the conversation."
            )

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": f"Please summarize this conversation:\n\n{conversation_history}",
                    },
                ],
                max_tokens=500,
                temperature=0.3,
            )

            content = response.choices[0].message.content
            # Ensure we always return a string
            return content if content is not None else ""
        except Exception as e:
            logger.error(f"Error compressing chat history: {e}")
            # If compression fails, return truncated original
            tokens = ENCODING.encode(conversation_history)
            if len(tokens) > MAX_TOKENS_FOR_CONTEXT:
                # Truncate to max tokens and decode back to string
                tokens = tokens[:MAX_TOKENS_FOR_CONTEXT]
                return ENCODING.decode(tokens) + "\n...(truncated)"

            return conversation_history

    @staticmethod
    def get_conversation_context(session_id: str) -> str:
        """Get the full conversation context for the session"""
        session_data = SessionMemory.get_session(session_id)
        if not session_data:
            logger.warning(f"No context found for session: {session_id}")
            return ""

        context = ""
        # Add compressed summary if it exists
        if session_data["compressed_summary"]:
            context += "Previous conversation summary:\n" + session_data["compressed_summary"] + "\n\n"

        # Add recent turns
        context += "Recent conversation:\n"
        for turn in session_data["recent_turns"]:
            context += f"User: {turn['user']}\nAI: {turn['ai']}\n\n"

        return context.strip()

    @staticmethod
    def delete_session(session_id: str) -> None:
        """Delete a session"""
        try:
            redis_client.delete(SessionMemory.get_session_key(session_id))
            logger.info(f"Deleted session: {session_id}")
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            raise
