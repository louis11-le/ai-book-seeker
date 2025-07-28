"""
ChromaDB Service for Vector Storage Management

This module provides a comprehensive service for managing ChromaDB vector storage
with LangChain integration, supporting multiple collections and flexible operations.

Features:
- Multi-collection support with flexible naming
- Automatic collection caching and management
- Comprehensive CRUD operations for documents
- Health monitoring and collection information
- Error handling and structured logging
- Input validation and type safety
- Proper separation of different data types (books vs FAQs)
"""

from typing import Any, Dict, List, Optional, Tuple

from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_core.documents import Document

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


class ChromaDBService:
    """
    Enhanced service for managing persistent vector storage and search with LangChain's Chroma.

    This service provides a unified interface for managing multiple ChromaDB collections,
    supporting flexible naming, caching, and comprehensive vector operations.

    Key Features:
    - Multi-collection support with flexible naming
    - Automatic collection caching and management
    - Comprehensive CRUD operations for documents
    - Health monitoring and collection information
    - Error handling and structured logging
    - Input validation and type safety
    - Backward compatibility with legacy code
    - Proper separation of different data types (books vs FAQs)
    """

    def __init__(
        self,
        settings: AppSettings,
        embedding_provider: Any,
    ) -> None:
        """
        Initialize the ChromaDB service.

        Args:
            settings: Application settings containing ChromaDB configuration
            embedding_provider: LangChain embedding provider instance

        Note:
            This service now properly handles multiple persist directories:
            - Books: settings.chromadb.book_persist_directory
            - FAQs: settings.chromadb.faq_persist_directory
            Each collection type uses its appropriate directory.
        """
        self.settings = settings
        self.embedding_provider = embedding_provider

        # Cache for all collections (no "primary" concept)
        self._collections: Dict[str, Chroma] = {}

    def _get_persist_directory_for_collection(self, collection_name: str) -> str:
        """
        Get the appropriate persist directory for a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            str: The persist directory path for this collection type
        """
        # Map collection names to their appropriate persist directories
        if collection_name == self.settings.chromadb.book_collection_name:
            return self.settings.chromadb.book_persist_directory
        elif collection_name == self.settings.chromadb.faq_collection_name:
            return self.settings.chromadb.faq_persist_directory
        else:
            # For any other collections, use a default directory
            # This maintains backward compatibility
            logger.warning(f"Unknown collection '{collection_name}', using default persist directory")
            return self.settings.chromadb.book_persist_directory

    # ============================================================================
    # Collection Management Methods
    # ============================================================================

    def get_collection(self, name: str) -> Optional[Chroma]:
        """
        Get an existing collection by name.

        Args:
            name: Collection name

        Returns:
            Optional[Chroma]: The collection instance if it exists, None otherwise
        """
        if not name or not isinstance(name, str):
            logger.error(f"Invalid collection name: {name}")
            return None

        # Check if it's in our cache
        if name in self._collections:
            return self._collections[name]

        # Check if it exists in ChromaDB
        try:
            persist_directory = self._get_persist_directory_for_collection(name)
            client = PersistentClient(path=persist_directory)
            existing_collections = [col.name for col in client.list_collections()]

            if name in existing_collections:
                # Collection exists, create LangChain wrapper
                collection = Chroma(
                    collection_name=name,
                    embedding_function=self.embedding_provider,
                    persist_directory=persist_directory,
                )
                self._collections[name] = collection
                logger.debug(f"Retrieved existing ChromaDB collection: {name} from {persist_directory}")
                return collection
        except Exception as e:
            logger.error(f"Failed to check for existing collection {name}: {e}", exc_info=True)
            return None

    def create_collection(self, name: str) -> Chroma:
        """
        Create a new collection with the specified name.

        Args:
            name: Collection name

        Returns:
            Chroma: The newly created collection instance

        Raises:
            ValueError: If collection already exists or name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid collection name: {name}")

        # Check if it already exists in our cache
        if name in self._collections:
            raise ValueError(f"Collection '{name}' already exists in cache")

        # Check if it exists in ChromaDB
        existing_collection = self.get_collection(name)
        if existing_collection:
            raise ValueError(f"Collection '{name}' already exists in ChromaDB")

        # Create new collection with appropriate persist directory
        persist_directory = self._get_persist_directory_for_collection(name)
        collection = Chroma(
            collection_name=name,
            embedding_function=self.embedding_provider,
            persist_directory=persist_directory,
        )
        self._collections[name] = collection
        logger.info(f"Created new ChromaDB collection: {name} in {persist_directory}")
        return collection

    def get_or_create_collection(self, name: str) -> Chroma:
        """
        Get an existing collection or create it if it doesn't exist.

        Args:
            name: Collection name

        Returns:
            Chroma: The collection instance
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid collection name: {name}")

        # Try to get existing collection
        collection = self.get_collection(name)
        if collection:
            return collection

        # Create new collection if it doesn't exist
        return self.create_collection(name)

    def list_collections(self) -> List[str]:
        """
        List all available collections from all persist directories.

        Returns:
            List[str]: List of collection names
        """
        all_collections = set()

        try:
            # Check book persist directory
            book_client = PersistentClient(path=self.settings.chromadb.book_persist_directory)
            book_collections = [col.name for col in book_client.list_collections()]
            all_collections.update(book_collections)

            # Check FAQ persist directory
            faq_client = PersistentClient(path=self.settings.chromadb.faq_persist_directory)
            faq_collections = [col.name for col in faq_client.list_collections()]
            all_collections.update(faq_collections)

            return list(all_collections)
        except Exception as e:
            logger.error(f"Failed to list collections: {e}", exc_info=True)
            return []

    def get_collection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a collection.

        Args:
            name: Collection name

        Returns:
            Optional[Dict[str, Any]]: Collection information or None if not found
        """
        if not name or not isinstance(name, str):
            logger.error(f"Invalid collection name: {name}")
            return None

        try:
            collection = self.get_collection(name)
            if collection is None:
                return None

            collection_data = collection.get()
            count = len(collection_data["ids"]) if collection_data["ids"] else 0
            persist_directory = self._get_persist_directory_for_collection(name)

            return {
                "name": name,
                "count": count,
                "persist_directory": persist_directory,
                "collection_type": "books" if name == self.settings.chromadb.book_collection_name else "faqs",
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {name}: {e}", exc_info=True)
            return None

    def check_documents_exist(self, ids: List[str], collection_name: str) -> Dict[str, List[str]]:
        """
        Check which documents exist in a collection by their IDs.

        Args:
            ids: List of document IDs to check
            collection_name: Collection name

        Returns:
            Dict[str, List[str]]: Dictionary with 'existing' and 'missing' ID lists

        Raises:
            ValueError: If collection_name is invalid or ids list is empty
        """
        if not ids:
            raise ValueError("IDs list cannot be empty")

        if not isinstance(collection_name, str) or not collection_name.strip():
            raise ValueError(f"Invalid collection name: {collection_name}")

        try:
            collection = self.get_or_create_collection(collection_name)
            collection_data = collection.get()
            existing_ids = set(collection_data.get("ids", []))

            existing = [doc_id for doc_id in ids if doc_id in existing_ids]
            missing = [doc_id for doc_id in ids if doc_id not in existing_ids]

            return {"existing": existing, "missing": missing}
        except Exception as e:
            logger.error(f"Failed to check document existence in collection {collection_name}: {e}", exc_info=True)
            raise

    # ============================================================================
    # Specialized Collection Access Methods
    # ============================================================================

    def get_books_collection(self) -> Chroma:
        """
        Get the books collection for book embeddings.

        Returns:
            Chroma: The books collection
        """
        book_collection_name = self.settings.chromadb.book_collection_name
        collection = self.get_collection(book_collection_name)
        if collection is None:
            # Create the books collection if it doesn't exist
            collection = self.create_collection(book_collection_name)
        return collection

    def get_faqs_collection(self) -> Chroma:
        """
        Get the FAQs collection for FAQ embeddings.

        Returns:
            Chroma: The FAQs collection
        """
        faq_collection_name = self.settings.chromadb.faq_collection_name
        collection = self.get_collection(faq_collection_name)
        if collection is None:
            # Create the FAQ collection if it doesn't exist
            collection = self.create_collection(faq_collection_name)
        return collection

    # ============================================================================
    # Document Operations
    # ============================================================================

    def add_documents(self, documents: List[Document], collection_name: str, ids: Optional[List[str]] = None) -> None:
        """
        Add a list of LangChain Document objects to the vector store.

        Args:
            documents: List of LangChain Document objects
            collection_name: Collection name (required)
            ids: Optional list of document IDs

        Raises:
            ValueError: If collection_name is invalid or documents list is empty
            Exception: If document addition fails
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")

        if not isinstance(collection_name, str) or not collection_name.strip():
            raise ValueError(f"Invalid collection name: {collection_name}")

        try:
            collection = self.get_or_create_collection(collection_name)
            collection.add_documents(documents=documents, ids=ids)
            logger.debug(f"Added {len(documents)} documents to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma vector store: {e}", exc_info=True)
            raise

    def query(
        self, query: str, collection_name: str, k: int = 3, filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Query the vector store for documents similar to the query string.

        Args:
            query: Query string to search for
            collection_name: Collection name (required)
            k: Number of results to return (default: 3)
            filter: Optional metadata filter

        Returns:
            List[Document]: List of matching documents

        Raises:
            ValueError: If query is empty, k is invalid, or collection_name is invalid
            Exception: If query operation fails
        """
        if not query or not isinstance(query, str):
            raise ValueError(f"Invalid query: {query}")

        if k <= 0:
            raise ValueError(f"Invalid k value: {k}")

        if not isinstance(collection_name, str) or not collection_name.strip():
            raise ValueError(f"Invalid collection name: {collection_name}")

        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.similarity_search(query, k=k, filter=filter)
            logger.debug(f"Query '{query[:50]}...' returned {len(results)} results from collection: {collection_name}")
            return results
        except Exception as e:
            logger.error(f"Failed to query Chroma vector store: {e}", exc_info=True)
            raise

    def query_with_score(
        self, query: str, collection_name: str, k: int = 3, filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Query the vector store for documents similar to the query string with similarity scores.

        Args:
            query: Query string to search for
            collection_name: Collection name (required)
            k: Number of results to return (default: 3)
            filter: Optional metadata filter

        Returns:
            List[Tuple[Document, float]]: List of (document, score) tuples

        Raises:
            ValueError: If query is empty, k is invalid, or collection_name is invalid
            Exception: If query operation fails
        """
        if not query or not isinstance(query, str):
            raise ValueError(f"Invalid query: {query}")

        if k <= 0:
            raise ValueError(f"Invalid k value: {k}")

        if not isinstance(collection_name, str) or not collection_name.strip():
            raise ValueError(f"Invalid collection name: {collection_name}")

        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.similarity_search_with_score(query, k=k, filter=filter)
            logger.debug(
                f"Query '{query[:50]}...' returned {len(results)} results with scores from collection: {collection_name}"
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query Chroma vector store with scores: {e}", exc_info=True)
            raise

    def delete(self, ids: List[str], collection_name: str) -> None:
        """
        Delete documents from a collection by their IDs.

        Args:
            ids: List of document IDs to delete
            collection_name: Collection name (required)

        Raises:
            ValueError: If collection_name is invalid or ids list is empty
            Exception: If deletion fails
        """
        if not ids:
            raise ValueError("IDs list cannot be empty")

        if not isinstance(collection_name, str) or not collection_name.strip():
            raise ValueError(f"Invalid collection name: {collection_name}")

        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} documents from collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete documents from Chroma vector store: {e}", exc_info=True)
            raise

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_batch_size(self) -> int:
        """
        Get the batch size for operations.

        Returns:
            int: Batch size from settings
        """
        return self.settings.batch_size

    def get_books_collection_name(self) -> str:
        """
        Get the books collection name.

        Returns:
            str: Books collection name from settings
        """
        return self.settings.chromadb.book_collection_name

    def get_settings(self) -> AppSettings:
        """
        Get the application settings.

        Returns:
            AppSettings: Application settings
        """
        return self.settings

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the ChromaDB service.

        Returns:
            Dict[str, Any]: Health check results with status and collection information
        """
        try:
            # Test collections from both persist directories
            collections = self.list_collections()

            # Test main collections
            books_collection = self.get_books_collection()
            faqs_collection = self.get_faqs_collection()

            books_data = books_collection.get()
            faqs_data = faqs_collection.get()
            books_count = len(books_data["ids"]) if books_data["ids"] else 0
            faqs_count = len(faqs_data["ids"]) if faqs_data["ids"] else 0

            return {
                "status": "healthy",
                "persist_directories": {
                    "books": self.settings.chromadb.book_persist_directory,
                    "faqs": self.settings.chromadb.faq_persist_directory,
                },
                "total_collections": len(collections),
                "collections": collections,
                "books_collection_count": books_count,
                "faqs_collection_count": faqs_count,
            }
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}", exc_info=True)
            return {"status": "unhealthy", "error": str(e)}
