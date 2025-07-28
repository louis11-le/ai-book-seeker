"""
FAQService: Handles FAQ knowledge base search (semantic and keyword).

This module provides a comprehensive service for managing FAQ knowledge base operations,
including file parsing, vector indexing, semantic search, and keyword search.
All logging follows project-wide structured logging best practices.

Features:
- Loads and parses FAQ files from a directory structure
- Indexes FAQs in ChromaDB vector store for semantic search
- Supports both semantic and keyword search with unified interface
- Provides comprehensive error handling and logging

Search Interface:
- semantic_search_faqs_async(): Primary async semantic search method
- search_faqs(): Pure keyword search (no semantic matching)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.utils.chromadb_service import ChromaDBService
from ai_book_seeker.utils.langchain_embedder import create_embedder

logger = get_logger(__name__)

# Constants
DEFAULT_TOP_K = 3
DEFAULT_SEMANTIC_THRESHOLD = 0.5
FAQ_ID_SEPARATOR = ":"
SIMILARITY_BASE = 1.0
FAQ_QUESTION_PREFIX = "Q:"
FAQ_ANSWER_PREFIX = "A:"


class FAQService:
    """
    Service for handling FAQ knowledge base search (semantic and keyword).

    - Loads and parses FAQ files from a directory.
    - Indexes FAQs in a vector store (ChromaDB via enhanced service) for semantic search.
    - Supports both keyword and semantic search over FAQs.

    Search Methods:
    - semantic_search_faqs_async(): Primary async semantic search method
    - search_faqs(): Pure keyword search (no semantic matching)
    """

    def __init__(self, kb_dir: str, settings: AppSettings, chromadb_service: ChromaDBService) -> None:
        """
        Initialize the FAQService. Does not perform async work.

        Args:
            kb_dir: Path to the directory containing FAQ .txt files.
            settings: Application settings for embedder configuration (required).
            chromadb_service: ChromaDB service instance (required).

        Raises:
            FileNotFoundError: If the knowledge base directory does not exist.
            ValueError: If required settings are missing.
        """
        if not Path(kb_dir).exists():
            raise FileNotFoundError(f"Knowledge base directory does not exist: {kb_dir}")

        self.kb_dir = Path(kb_dir)
        self.settings = settings
        self.chromadb_service = chromadb_service
        self._indexed = False

        # Load FAQs after validation
        self.faqs = self.get_all_faqs()

    @classmethod
    async def async_init(cls, kb_dir: str, settings: AppSettings, chromadb_service: ChromaDBService) -> "FAQService":
        """
        Async factory method to create and initialize FAQService with async indexing.

        Args:
            kb_dir: Path to the directory containing FAQ .txt files.
            settings: Application settings for embedder configuration.
            chromadb_service: ChromaDB service instance.

        Returns:
            FAQService: Fully initialized service with indexed FAQs.

        Raises:
            FileNotFoundError: If the knowledge base directory does not exist.
            RuntimeError: If FAQ indexing fails.
        """
        self = cls(kb_dir, settings, chromadb_service)
        await self._index_faqs()
        self._indexed = True
        return self

    def _parse_faq_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """
        Parse a single FAQ file into a list of (question, answer) tuples.
        Expects Q: ... and A: ... pairs, separated by blank lines.

        Args:
            file_path: Path to the FAQ file to parse.

        Returns:
            List[Tuple[str, str]]: List of (question, answer) tuples.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnicodeDecodeError: If the file cannot be decoded as UTF-8.
        """
        faqs = []
        question: Optional[str] = None
        answer: Optional[str] = None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(FAQ_QUESTION_PREFIX):
                        question = line[len(FAQ_QUESTION_PREFIX) :].strip()
                    elif line.startswith(FAQ_ANSWER_PREFIX):
                        answer = line[len(FAQ_ANSWER_PREFIX) :].strip()
                    elif line == "" and question and answer is not None:
                        faqs.append((question, answer))
                        question = None
                        answer = None
                # Catch last Q/A pair if file does not end with blank line
                if question and answer is not None:
                    faqs.append((question, answer))
        except FileNotFoundError:
            logger.error(f"FAQ file not found: {file_path}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode FAQ file {file_path}: {e}", exc_info=True)
            return []

        return faqs

    def get_all_faqs(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Load and parse all FAQ files in the knowledge base directory.

        Returns:
            Dict[str, List[Tuple[str, str]]]: Dictionary mapping category (filename stem)
            to list of (question, answer) tuples.

        Raises:
            FileNotFoundError: If no FAQ files are found in the directory.
        """
        faqs = {}
        faq_files = list(self.kb_dir.glob("*.txt"))

        if not faq_files:
            logger.warning(f"No FAQ files found in directory: {self.kb_dir}")
            return faqs

        for file in faq_files:
            try:
                faqs[file.stem] = self._parse_faq_file(file)
                logger.debug(f"Loaded FAQ file: {file.name} with {len(faqs[file.stem])} Q&A pairs")
            except (FileNotFoundError, UnicodeDecodeError) as e:
                logger.error(f"Failed to load FAQ file {file.name}: {e}", exc_info=True)
                # Continue loading other files even if one fails
                continue

        return faqs

    def _flatten_faqs_for_indexing(self) -> List[Tuple[str, str, str, str]]:
        """
        Flatten all FAQs to (id, category, question, answer) tuples for indexing.

        Returns:
            List[Tuple[str, str, str, str]]: List of (id, category, question, answer) tuples
        """
        faq_items = []
        for category, qas in self.faqs.items():
            for idx, (q, a) in enumerate(qas):
                faq_id = f"{category}{FAQ_ID_SEPARATOR}{idx}"
                faq_items.append((faq_id, category, q, a))
        return faq_items

    def _check_existing_documents(self, ids: List[str]) -> bool:
        """
        Check if all FAQ IDs are already present in the vector store.

        Args:
            ids: List of FAQ IDs to check.

        Returns:
            bool: True if all documents exist, False otherwise.
        """
        try:
            faq_collection_name = self.settings.chromadb.faq_collection_name
            doc_status = self.chromadb_service.check_documents_exist(ids, faq_collection_name)
            return not doc_status["missing"]
        except Exception as e:
            logger.warning(f"Could not check existing FAQ IDs: {e}", exc_info=True)
            return False

    def _create_documents_for_indexing(self, metadatas: List[Dict[str, str]]) -> List[Document]:
        """
        Create LangChain Document objects for indexing.

        Args:
            metadatas: List of metadata dictionaries.

        Returns:
            List[Document]: List of Document objects.
        """
        return [Document(page_content=metadata["question"], metadata=metadata) for metadata in metadatas]

    def _process_embedding_results(
        self, embeddings: List[Any], ids: List[str], metadatas: List[Dict[str, str]]
    ) -> Tuple[List[str], List[Dict[str, str]]]:
        """
        Process embedding results and filter out failed embeddings.

        Args:
            embeddings: List of embedding results.
            ids: List of FAQ IDs.
            metadatas: List of metadata dictionaries.

        Returns:
            Tuple[List[str], List[Dict[str, str]]]: Valid IDs and metadatas.

        Raises:
            RuntimeError: If all embeddings failed.
        """
        valid = [(i, emb) for i, emb in enumerate(embeddings) if emb is not None]
        if not valid:
            logger.error("All FAQ embeddings failed")
            raise RuntimeError("All FAQ embeddings failed - no valid embeddings generated")

        valid_ids = [ids[i] for i, _ in valid]
        valid_metadatas = [metadatas[i] for i, _ in valid]
        return valid_ids, valid_metadatas

    async def _index_faqs(self) -> None:
        """
        Index all FAQs in the vector store for semantic search.
        Embeds all questions and stores them as LangChain Document objects.
        Skips embedding if all FAQ IDs are already present in the vectorstore.

        Raises:
            RuntimeError: If embedding fails for all questions.
            ValueError: If FAQ collection is not available.
        """
        faq_items = self._flatten_faqs_for_indexing()
        if not faq_items:
            logger.warning("No FAQs to index: count=0")
            return

        ids = [item[0] for item in faq_items]
        questions = [item[2] for item in faq_items]
        metadatas = [{"category": item[1], "question": item[2], "answer": item[3]} for item in faq_items]

        # Check if all IDs are already present in the FAQ collection
        if self._check_existing_documents(ids):
            logger.info(f"All FAQ IDs already indexed: count={len(ids)}")
            return

        # Batch embed questions
        logger.info(f"Embedding FAQ questions: count={len(questions)}")

        embedder = create_embedder(self.settings)
        embeddings = await embedder.embed_texts(questions)

        # Process embedding results
        valid_ids, valid_metadatas = self._process_embedding_results(embeddings, ids, metadatas)

        # Create documents and add to ChromaDB
        documents = self._create_documents_for_indexing(valid_metadatas)

        try:
            faq_collection = self.chromadb_service.get_faqs_collection()
            faq_collection.add_documents(documents=documents, ids=valid_ids)
            logger.info(f"Indexed FAQs in ChromaDB: count={len(valid_ids)}")
        except ValueError as e:
            logger.error(f"Failed to access FAQ collection: {e}", exc_info=True)
            raise ValueError(f"FAQ collection not available: {e}")

    def _validate_query(self, query: str) -> None:
        """
        Validate that the query is not empty.

        Args:
            query: The search query string.

        Raises:
            ValueError: If query is empty or invalid.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

    def _process_semantic_results(
        self, results_with_score: List[Tuple[Document, float]], threshold: float, top_k: int
    ) -> List[Tuple[str, str, str, float]]:
        """
        Process semantic search results and apply threshold filtering.

        Args:
            results_with_score: List of (document, score) tuples.
            threshold: Minimum similarity threshold.
            top_k: Maximum number of results to return.

        Returns:
            List[Tuple[str, str, str, float]]: Processed results.
        """
        processed_results = []
        for doc, score in results_with_score:
            if doc.metadata and score is not None:
                similarity = SIMILARITY_BASE - score
                if similarity >= threshold:
                    processed_results.append(
                        (
                            doc.metadata.get("category", ""),
                            doc.metadata.get("question", ""),
                            doc.metadata.get("answer", ""),
                            similarity,
                        )
                    )

        processed_results.sort(key=lambda x: -x[3] if x[3] is not None else 0)
        return processed_results[:top_k]

    async def semantic_search_faqs_async(
        self, query: str, top_k: int = DEFAULT_TOP_K, threshold: float = DEFAULT_SEMANTIC_THRESHOLD
    ) -> List[Tuple[str, str, str, float]]:
        """
        Perform semantic search over FAQs using vector similarity.

        Args:
            query: Search query string.
            top_k: Maximum number of results to return.
            threshold: Minimum similarity threshold (0.0 to 1.0).

        Returns:
            List[Tuple[str, str, str, float]]: List of (category, question, answer, similarity) tuples.

        Raises:
            ValueError: If query is empty or invalid.
            RuntimeError: If FAQ collection is not available.
        """
        try:
            self._validate_query(query)
            logger.info(f"Semantic search called: query={query}")

            # Query ChromaDB using LangChain API
            try:
                faq_collection = self.chromadb_service.get_faqs_collection()
                results_with_score = faq_collection.similarity_search_with_score(query, k=top_k)
            except ValueError as e:
                logger.error(f"FAQ collection not available: {e}", exc_info=True)
                raise RuntimeError(f"FAQ collection not available: {e}")

            logger.info(f"Vector store results for query: query={query}, count={len(results_with_score)}")

            if not results_with_score:
                logger.info("No semantic matches found in ChromaDB")
                return []

            return self._process_semantic_results(results_with_score, threshold, top_k)

        except (ValueError, RuntimeError) as e:
            logger.error(f"Semantic search failed: error={str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in semantic search: error={str(e)}", exc_info=True)
            raise RuntimeError(f"Unexpected error in semantic search: {e}") from e

    def search_faqs(self, query: str) -> List[Tuple[str, str, str]]:
        """
        Perform a simple keyword search over all FAQs.

        Args:
            query: The search query string.

        Returns:
            List[Tuple[str, str, str]]: List of (category, question, answer) tuples matching the query.

        Raises:
            ValueError: If query is empty or invalid.
        """
        self._validate_query(query)
        logger.info(f"Keyword search called: query={query}")

        results = []
        query_lower = query.lower().strip()

        for category, qas in self.faqs.items():
            for q, a in qas:
                if query_lower in q.lower():
                    results.append((category, q, a))

        logger.info(f"Keyword search results: count={len(results)}")
        return results
