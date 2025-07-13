"""
FAQService: Handles FAQ knowledge base search (semantic and keyword).
All logging follows project-wide structured logging best practices.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.utils.chromadb_service import ChromaDBService
from ai_book_seeker.utils.langchain_embedder import embed_texts
from langchain_core.documents import Document

logger = get_logger(__name__)


class FAQService:
    """
    Service for handling FAQ knowledge base search (semantic and keyword).

    - Loads and parses FAQ files from a directory.
    - Indexes FAQs in a vector store (ChromaDB via LangChain) for semantic search.
    - Supports both keyword and semantic search over FAQs.
    """

    def __init__(self, kb_dir: str):
        """
        Initialize the FAQService. Does not perform async work.

        Args:
            kb_dir: Path to the directory containing FAQ .txt files.
        """

        self.kb_dir = Path(kb_dir)
        self.faqs = self.get_all_faqs()
        self.chromadb = ChromaDBService()
        self._indexed = False

    @classmethod
    async def async_init(cls, kb_dir: str):
        """
        Async factory method to create and initialize FAQService with async indexing.
        """
        self = cls(kb_dir)
        await self._index_faqs()
        self._indexed = True
        return self

    def _parse_faq_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """
        Parse a single FAQ file into a list of (question, answer) tuples.
        Expects Q: ... and A: ... pairs, separated by blank lines.
        """
        faqs = []
        question = None
        answer = None
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Q:"):
                    question = line[2:].strip()
                elif line.startswith("A:"):
                    answer = line[2:].strip()
                elif line == "" and question and answer is not None:
                    faqs.append((question, answer))
                    question = None
                    answer = None
            # Catch last Q/A pair if file does not end with blank line
            if question and answer is not None:
                faqs.append((question, answer))

        return faqs

    def get_all_faqs(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Load and parse all FAQ files in the knowledge base directory.

        Returns:
            Dictionary mapping category (filename stem) to list of (question, answer) tuples.
        """
        faqs = {}
        for file in self.kb_dir.glob("*.txt"):
            faqs[file.stem] = self._parse_faq_file(file)

        return faqs

    async def _index_faqs(self):
        """
        Index all FAQs in the vector store for semantic search.
        Embeds all questions and stores them as LangChain Document objects.
        Skips embedding if all FAQ IDs are already present in the vectorstore.
        """
        # Flatten all FAQs to (id, category, question, answer)
        faq_items = []
        for category, qas in self.faqs.items():
            for idx, (q, a) in enumerate(qas):
                faq_id = f"{category}:{idx}"
                faq_items.append((faq_id, category, q, a))

        if not faq_items:
            logger.warning("no_faqs_to_index: count=0")
            return

        ids = [item[0] for item in faq_items]
        questions = [item[2] for item in faq_items]
        metadatas = [{"category": item[1], "question": item[2], "answer": item[3]} for item in faq_items]

        # Check if all IDs are already present in the vectorstore
        try:
            existing_docs = self.chromadb.vectorstore.get(ids=ids)
            existing_ids = set(existing_docs.get("ids", [])) if isinstance(existing_docs, dict) else set()
            if set(ids).issubset(existing_ids):
                logger.info(f"all_faq_ids_already_indexed: count={len(ids)}")
                return
        except Exception as e:
            logger.warning(f"could_not_check_existing_vectorstore_ids: error={str(e)}")

        # Debug: Log all questions being embedded
        logger.info(f"questions_being_embedded: count={len(questions)}")
        # Batch embed questions
        logger.info(f"embedding_faq_questions: count={len(questions)}")
        embeddings = await embed_texts(questions)
        # Remove any failed embeddings
        valid = [(i, emb) for i, emb in enumerate(embeddings) if emb is not None]
        if not valid:
            logger.error("all_faq_embeddings_failed")
            return

        valid_ids = [ids[i] for i, _ in valid]
        valid_metadatas = [metadatas[i] for i, _ in valid]
        # Create LangChain Document objects
        documents = [
            Document(page_content=valid_metadatas[i]["question"], metadata=valid_metadatas[i])
            for i in range(len(valid_metadatas))
        ]
        # Add to ChromaDB using new API
        self.chromadb.add_documents(documents, ids=valid_ids)
        logger.info(f"indexed_faqs_in_chromadb: count={len(valid_ids)}")
        # Debug: Log all indexed questions
        logger.info(f"indexed_questions: count={len(documents)}")

    async def semantic_search_faqs_async(
        self, query: str, top_k: int = 3, threshold: float = 0.3
    ) -> List[Tuple[str, str, str, float]]:
        """
        Perform semantic search over FAQs using vector similarity.
        """
        try:
            logger.info(f"semantic_search_faqs_async called: query={query}")
            results_with_score = self.chromadb.query_with_score(query, k=top_k)

            logger.info(f"vectorstore_results_for_query: query={query}, count={len(results_with_score)}")
            logger.info(f"results_with_score: results_with_score={results_with_score}")

            if not results_with_score:
                logger.info("no_semantic_matches_found_in_chromadb")
                return []

            all_scores_none = all(score is None for _, score in results_with_score)
            results = []
            for doc, score in results_with_score:
                meta = doc.metadata
                similarity = 1.0 - score if score is not None else 0.0
                if score is not None and similarity >= threshold:
                    results.append(
                        (meta.get("category", ""), meta.get("question", ""), meta.get("answer", ""), similarity)
                    )
                elif all_scores_none:
                    q = meta.get("question", "").lower()
                    a = meta.get("answer", "").lower()
                    if query.lower() in q or query.lower() in a:
                        results.append(
                            (meta.get("category", ""), meta.get("question", ""), meta.get("answer", ""), None)
                        )
            # If all scores are None and no results matched the query, return an empty list
            if all_scores_none and not results:
                return []

            results.sort(key=lambda x: -x[3] if x[3] is not None else 0)
            return results[:top_k]
        except Exception as e:
            logger.error(f"semantic_search_failed: error={str(e)}", exc_info=True)
            return []

    def search_faqs(self, query: str) -> List[Tuple[str, str, str]]:
        """
        Perform a simple keyword search over all FAQs.

        Args:
            query: The search query string.
        Returns:
            List of (category, question, answer) tuples matching the query.
        """
        logger.info(f"search_faqs simple keyword called: query={query}")
        results = []
        for category, qas in self.faqs.items():
            for q, a in qas:
                match = query.lower() in q.lower()
                if match:
                    results.append((category, q, a))

        logger.info(f"search_faqs simple keyword count: count={len(results)}")
        logger.info(f"search_faqs simple keyword results: results={results}")

        return results

    def semantic_search_faqs(
        self, query: str, top_k: int = 3, threshold: float = 0.5
    ) -> List[Tuple[str, str, str, float]]:
        """
        Synchronous wrapper for async semantic search.
        Falls back to keyword search if semantic search fails.

        Args:
            query: The search query string.
            top_k: Number of top results to return.
            threshold: Minimum similarity threshold (if available).
        Returns:
            List of (category, question, answer, similarity) tuples.
        """
        try:
            return asyncio.run(self.semantic_search_faqs_async(query, top_k, threshold))
        except Exception as e:
            logger.error(f"semantic_search_sync_failed: error={str(e)}", exc_info=True)
            # Fallback to keyword search
            keyword_results = self.search_faqs(query)
            return [(cat, q, a, 1.0) for (cat, q, a) in keyword_results][:top_k]
