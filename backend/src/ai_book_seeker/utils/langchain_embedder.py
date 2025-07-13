"""
Async utility for embedding text(s) using LangChain's Embedding interface.

- Uses LangChain's OpenAIEmbeddings by default, but is structured for easy provider swapping.
- Supports async embedding for single and batch text.
- Reads model and API key from environment variables.
- Add your own provider by swapping the Embedding class import and instantiation.
"""

# LangSmith tracing: If LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY are set in the environment,
# all LangChain embedding calls will be traced and visible in your LangSmith dashboard.

import asyncio
import os
from typing import List, Optional

from ai_book_seeker.core.logging import get_logger
from langchain_openai import OpenAIEmbeddings

logger = get_logger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not set. Embedding calls will fail.")
    raise RuntimeError("OPENAI_API_KEY not set. Please set the environment variable.")

# Provider abstraction: swap this class to change providers (e.g., HuggingFaceEmbeddings)
EmbeddingProvider = OpenAIEmbeddings

# Instantiate the embedding model
embedder = EmbeddingProvider(model=OPENAI_EMBEDDING_MODEL)


async def embed_text(text: str) -> Optional[List[float]]:
    """
    Async embed a single text string using LangChain's embedding interface.
    Returns the embedding vector as a list of floats, or None if failed.
    """
    loop = asyncio.get_event_loop()
    try:
        # LangChain's embed_query is sync, so run in thread pool
        embedding = await loop.run_in_executor(None, embedder.embed_query, text)
        return embedding
    except Exception as e:
        logger.error(f"LangChain embedding failed: {e}", exc_info=True)
        return None


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Async embed a list of texts using LangChain's embedding interface.
    Returns a list of embeddings (raises on error).
    """
    loop = asyncio.get_event_loop()
    try:
        # LangChain's embed_documents is sync, so run in thread pool
        embeddings = await loop.run_in_executor(None, embedder.embed_documents, texts)
        return embeddings
    except Exception as e:
        logger.error(f"LangChain batch embedding failed: {e}", exc_info=True)
        raise
