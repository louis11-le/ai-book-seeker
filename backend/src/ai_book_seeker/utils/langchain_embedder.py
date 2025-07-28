"""
Async utility for embedding text(s) using LangChain's Embedding interface.

- Uses LangChain's OpenAIEmbeddings by default, but is structured for easy provider swapping.
- Supports async embedding for single and batch text.
- Reads model and API key from centralized AppSettings config (see core/config.py).
- All configuration (API key, model) must be set via AppSettings, not direct environment variable access.
- To override config for testing, patch AppSettings or use environment variables before import.
"""

# LangSmith tracing: If LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY are set in the environment,
# all LangChain embedding calls will be traced and visible in your LangSmith dashboard.

import asyncio
from typing import List, Optional

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from langchain_openai import OpenAIEmbeddings

logger = get_logger(__name__)

# Provider abstraction: swap this class to change providers (e.g., HuggingFaceEmbeddings)
EmbeddingProvider = OpenAIEmbeddings


def create_embedder(settings: AppSettings) -> "LangChainEmbedder":
    """
    Factory function to create a LangChainEmbedder instance with the provided settings.

    Args:
        settings: Application settings containing OpenAI configuration

    Returns:
        LangChainEmbedder: Configured embedder instance
    """
    return LangChainEmbedder(settings)


class LangChainEmbedder:
    """
    Async utility for embedding text(s) using LangChain's Embedding interface.
    """

    def __init__(self, settings: AppSettings):
        """
        Initialize LangChainEmbedder with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._embedder = None

    def _get_embedder(self):
        """
        Get or create the embedding provider instance.

        This function performs lazy initialization and validates the API key
        only when the embedder is actually needed, not at import time.
        """
        if self._embedder is None:
            # Use embedding_model if present, else fallback to model (from config)
            embedding_model = getattr(self.settings.openai, "embedding_model", self.settings.openai.model)

            # Validate API key only when embedder is created
            if not self.settings.openai.api_key.get_secret_value():
                logger.error("OPENAI_API_KEY not set in config. Embedding calls will fail.")
                raise RuntimeError("OPENAI_API_KEY not set. Please set it in your .env or environment.")

            # Instantiate the embedding model (model from config)
            # The OpenAI API key must be set in the environment (AppSettings loads it from .env)
            self._embedder = EmbeddingProvider(model=embedding_model)
            logger.debug(f"Embedding provider initialized with model: {embedding_model}")

        return self._embedder

    async def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Async embed a single text string using LangChain's embedding interface.
        Returns the embedding vector as a list of floats, or None if failed.
        """
        loop = asyncio.get_event_loop()
        try:
            # Get embedder (lazy initialization)
            embedder = self._get_embedder()
            # LangChain's embed_query is sync, so run in thread pool
            embedding = await loop.run_in_executor(None, embedder.embed_query, text)
            return embedding
        except Exception as e:
            logger.error(f"LangChain embedding failed: {e}", exc_info=True)
            return None

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Async embed a list of texts using LangChain's embedding interface.
        Returns a list of embeddings (raises on error).
        """
        loop = asyncio.get_event_loop()
        try:
            # Get embedder (lazy initialization)
            embedder = self._get_embedder()
            # LangChain's embed_documents is sync, so run in thread pool
            embeddings = await loop.run_in_executor(None, embedder.embed_documents, texts)
            return embeddings
        except Exception as e:
            logger.error(f"LangChain batch embedding failed: {e}", exc_info=True)
            raise
