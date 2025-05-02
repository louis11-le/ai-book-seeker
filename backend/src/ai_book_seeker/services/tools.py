"""
AI Book Seeker OpenAI Function Calling Tools

This module provides tool functions that OpenAI function calling can use for
AI Book Seeker's chatbot. These are specifically formatted with Pydantic models
to match OpenAI's function calling schema.
"""

from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_book_seeker.core.config import OPENAI_API_KEY, OPENAI_MODEL
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.services.explainer import BookPreferences
from ai_book_seeker.services.query import search_books as db_search_books

# Set up logging
logger = get_logger("tools")

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Get model from environment
if not OPENAI_MODEL:
    logger.error("OPENAI_MODEL environment variable is required")
    raise ValueError("OPENAI_MODEL environment variable is required")


class SearchBooksParams(BaseModel):
    age: Optional[int] = Field(None, description="The age of the reader")
    purpose: Optional[str] = Field(None, description="The purpose of the book (learning, entertainment)")
    budget: Optional[float] = Field(None, description="The budget for buying books")
    genre: Optional[str] = Field(None, description="The preferred genre")


class BookResult(BaseModel):
    id: int
    title: str
    author: str
    description: str
    from_age: Optional[int] = None
    to_age: Optional[int] = None
    purpose: str
    genre: str
    price: float
    tags: List[str]
    reason: Optional[str] = None


# Tool definitions
# Using explicit type annotations to match OpenAI's expected format
search_books_tool: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "search_books",
        "description": "Search books that match user preferences",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "The age of the reader"},
                "purpose": {
                    "type": "string",
                    "description": "The purpose of the book (learning, entertainment)",
                },
                "budget": {
                    "type": "number",
                    "description": "The budget for buying books",
                },
                "genre": {
                    "type": "string",
                    "description": "The preferred genre (optional)",
                },
            },
            "required": [],
        },
    },
}


# Tool implementation
def search_books(db: Session, params: SearchBooksParams) -> List[BookResult]:
    """
    Search for books based on provided parameters.
    """
    # Create BookPreferences from the params
    preferences = BookPreferences(
        age=params.age,
        purpose=params.purpose,
        budget=params.budget,
        genre=params.genre,
        query_text=None,  # No query text from function calling
    )

    # Search for books directly
    book_dicts = db_search_books(db, preferences)

    # Convert to BookResult objects
    book_results = []
    for book_dict in book_dicts:
        # Convert tags string to list
        tag_list = []
        if book_dict.get("tags"):
            tag_list = [tag.strip() for tag in book_dict["tags"].split(",")]

        book_results.append(
            BookResult(
                id=int(book_dict["id"]),
                title=str(book_dict["title"]),
                author=str(book_dict["author"]),
                description=str(book_dict.get("description", "")),
                from_age=int(book_dict.get("from_age", 0)),
                to_age=int(book_dict.get("to_age", 0)),
                purpose=str(book_dict.get("purpose", "")),
                genre=str(book_dict.get("genre", "")),
                price=float(book_dict["price"]) if book_dict.get("price") else 0.0,
                tags=tag_list,
                reason=book_dict.get("explanation", None),
            )
        )

    return book_results


# List of available tools
available_tools = [search_books_tool]
