"""
ChromaDB utility using LangChain's Chroma vector store abstraction.

- Uses LangChain's Chroma for vector storage and search.
- Uses OpenAIEmbeddings by default, but is structured for easy provider swapping.
- Supports persistence and collection naming via environment variables.
- Provides methods for adding, querying, and deleting documents/embeddings.
"""

import os
from typing import Any, Dict, List, Optional

from ai_book_seeker.core.logging import get_logger
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

logger = get_logger(__name__)

CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./chromadb_faq")
CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "faq_embeddings")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")


class ChromaDBService:
    """
    Service for managing persistent vector storage and search with LangChain's Chroma.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[Any] = None,
    ):
        self.persist_directory = persist_directory or CHROMADB_PATH
        self.collection_name = collection_name or CHROMADB_COLLECTION
        self.embedding_provider = embedding_provider or OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_provider,
            persist_directory=self.persist_directory,
        )

    def add_documents(self, documents: List[Document], ids: Optional[List[str]] = None):
        """
        Add a list of LangChain Document objects to the vector store.
        Optionally specify IDs for the documents.
        """
        try:
            self.vectorstore.add_documents(documents=documents, ids=ids)
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma vector store: {e}", exc_info=True)

    def query(self, query: str, k: int = 3, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Query the vector store for documents similar to the query string.
        Returns a list of LangChain Document objects.
        """
        try:
            results = self.vectorstore.similarity_search(query, k=k, filter=filter)
            return results
        except Exception as e:
            logger.error(f"Chroma vector store query failed: {e}", exc_info=True)
            return []

    def query_with_score(self, query: str, k: int = 3, filter: Optional[Dict[str, Any]] = None) -> List[tuple]:
        """
        Query the vector store for documents similar to the query string and return (Document, score) tuples.
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k, filter=filter)
            return results
        except Exception as e:
            logger.error(f"Chroma vector store query with score failed: {e}", exc_info=True)
            return []

    def delete(self, ids: List[str]):
        """
        Delete documents/embeddings from the vector store by IDs.
        """
        try:
            self.vectorstore.delete(ids=ids)
        except Exception as e:
            logger.error(f"Failed to delete documents from Chroma vector store: {e}", exc_info=True)
