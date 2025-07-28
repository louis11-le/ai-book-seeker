"""
Vector Database Module for AI Book Seeker

This module handles the vector database operations for storing and retrieving book embeddings.
It uses ChromaDB as the vector store and OpenAI's embeddings for vector generation.
All configuration is accessed via the centralized AppSettings config object.
"""

from typing import Any, List

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book
from langchain_core.documents import Document
from openai import OpenAI
from sqlalchemy.orm import Session

# Set up logging
logger = get_logger("vectordb")

# Constants
DEFAULT_SEARCH_LIMIT = 3
DEFAULT_SIMILARITY_THRESHOLD = 0.7
SIMILARITY_DIVISOR = 2.0
BOOK_ID_PREFIX = "book-"


def _format_book_content_for_embedding(book: Book) -> str:
    """
    Format book content for embedding generation.

    Args:
        book: Book object to format

    Returns:
        str: Formatted book content string
    """
    age_range = (
        f"{book.from_age}-{book.to_age}" if book.from_age is not None and book.to_age is not None else "All ages"
    )

    return (
        f"Title: {book.title} | Description: {book.description} | Age range: {age_range} | "
        f"Purpose: {book.purpose} | Genre: {book.genre or 'N/A'} | Tags: {book.tags}"
    )


def _extract_book_metadata(books: List[Book]) -> List[dict]:
    """
    Extract metadata from book objects for ChromaDB storage.

    Args:
        books: List of Book objects

    Returns:
        List[dict]: List of metadata dictionaries
    """
    metadatas = []
    for book in books:
        book_id_val = getattr(book, "id", None)
        if book_id_val is None:
            continue

        metadatas.append({"id": int(book_id_val), "title": str(getattr(book, "title", ""))})

    return metadatas


def _has_valid_search_results(results: Any) -> bool:
    """
    Check if search results contain valid metadata and distances.

    Args:
        results: Search results from ChromaDB

    Returns:
        bool: True if results contain valid data
    """
    return (
        results
        and "metadatas" in results
        and results["metadatas"]
        and len(results["metadatas"]) > 0
        and "distances" in results
        and results["distances"]
        and len(results["distances"]) > 0
    )


def create_openai_client(settings: AppSettings) -> OpenAI:
    """
    Create an OpenAI client instance using the provided settings.

    Args:
        settings: Application settings containing OpenAI configuration

    Returns:
        OpenAI: Configured OpenAI client instance
    """
    return OpenAI(api_key=settings.openai.api_key.get_secret_value())


def get_embedding(text: str, settings: AppSettings) -> List[float]:
    """
    Get embedding for a text using OpenAI API.

    Args:
        text: Text to embed
        settings: Application settings

    Returns:
        List[float]: Embedding vector
    """
    client = create_openai_client(settings)
    embedding_model = getattr(settings.openai, "embedding_model", settings.openai.model)
    response = client.embeddings.create(model=embedding_model, input=text)
    return response.data[0].embedding


def create_book_embeddings_from_database(db: Session, chromadb_service: Any) -> None:
    """
    Create book embeddings from database records and store them in the vector database.

    This function loads books from the database, creates embeddings for their content,
    and stores them in the ChromaDB vector store. Existing embeddings are skipped.
    Batch size is controlled by config (settings.batch_size).

    Args:
        db: Database session
        chromadb_service: ChromaDB client service instance
    """
    books = db.query(Book).all()
    logger.info(f"Creating embeddings for {len(books)} books from database")

    # Use centralized books collection
    book_collection = chromadb_service.get_books_collection()
    logger.info(f"Using ChromaDB collection: {chromadb_service.get_books_collection_name()}")

    try:
        existing_ids = set(book_collection.get(include=[])["ids"])
        logger.info(f"Found {len(existing_ids)} existing embeddings in ChromaDB")
    except Exception:
        existing_ids = set()
        logger.info("No existing embeddings found or error accessing ChromaDB")

    created_count = 0
    skipped_count = 0
    BATCH_SIZE = chromadb_service.get_batch_size()
    books_to_embed = []
    book_ids = []
    book_contents = []

    for book in books:
        # Book.id is a SQLAlchemy Column, ensure int conversion
        book_id_val = getattr(book, "id", None)
        if book_id_val is None:
            continue

        book_id = int(book_id_val)
        book_id_str = f"{BOOK_ID_PREFIX}{book_id}"
        if book_id_str in existing_ids:
            skipped_count += 1
            continue

        content_to_embed = _format_book_content_for_embedding(book)
        books_to_embed.append(book)
        book_ids.append(book_id_str)
        book_contents.append(content_to_embed)
        if len(books_to_embed) >= BATCH_SIZE:
            process_embedding_batch(
                books_to_embed, book_ids, book_contents, chromadb_service.get_settings(), book_collection
            )
            created_count += len(books_to_embed)
            books_to_embed = []
            book_ids = []
            book_contents = []

    if books_to_embed:
        process_embedding_batch(
            books_to_embed, book_ids, book_contents, chromadb_service.get_settings(), book_collection
        )
        created_count += len(books_to_embed)

    logger.info(f"Book embeddings creation complete: {created_count} created, {skipped_count} skipped")


def process_embedding_batch(
    books: List[Book], book_ids: List[str], contents: List[str], settings: AppSettings, book_collection: Any
) -> None:
    """
    Process a batch of books for embedding and storage in ChromaDB.
    Embedding model is selected from config.

    Args:
        books: List of Book objects
        book_ids: List of book ID strings
        contents: List of content strings to embed
        settings: Application settings
        book_collection: ChromaDB collection

    Raises:
        Exception: If embedding creation or storage fails
    """
    try:
        metadatas = _extract_book_metadata(books)
        # Create Document objects for the new langchain-chroma interface
        documents = [
            Document(page_content=content, metadata=metadata) for content, metadata in zip(contents, metadatas)
        ]

        # Add documents using the new interface
        book_collection.add_documents(
            documents=documents,
            ids=book_ids,
        )
        logger.debug(f"Added batch of {len(books)} embeddings to ChromaDB")
    except Exception as e:
        logger.error(f"Error creating embeddings batch: {e}", exc_info=True)
        raise


def search_by_vector(
    query_text: str,
    chromadb_service: Any,
    limit: int = DEFAULT_SEARCH_LIMIT,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> List[int]:
    """
    Search for books using vector similarity.

    Args:
        query_text: Text to search for
        chromadb_service: ChromaDB client service instance
        limit: Maximum number of results
        threshold: Similarity threshold

    Returns:
        List[int]: List of book IDs
    """
    try:
        book_collection = chromadb_service.get_books_collection()

        logger.debug(f"Searching ChromaDB for query: '{query_text[:50]}...' with limit: {limit}")

        # Use LangChain Chroma API instead of native ChromaDB API
        results_with_scores = book_collection.similarity_search_with_score(query_text, k=limit)

        logger.debug(f"ChromaDB search complete, results found: {bool(results_with_scores)}")
        book_ids: List[int] = []

        for document, score in results_with_scores:
            # Convert LangChain score to similarity (lower score = higher similarity)
            similarity = 1 - score  # LangChain returns distance, convert to similarity

            if "id" in document.metadata:
                id_val = document.metadata["id"]
                try:
                    id_int = int(id_val) if id_val is not None else None
                except Exception:
                    id_int = None

                if id_int is not None and similarity >= threshold:
                    book_ids.append(id_int)
                    logger.debug(f"Book {id_val}: similarity {similarity:.2f}")
                else:
                    logger.debug(f"Filtered out book {id_val} with low similarity {similarity:.2f}")

        logger.debug(f"Found {len(book_ids)} similar books for vector query: {query_text[:50]}...")
        return book_ids
    except Exception as e:
        logger.error(f"Error in vector search: {e}", exc_info=True)
        return []


def get_book_vector_matches(
    query_text: str, db: Session, chromadb_service: Any, limit: int = DEFAULT_SEARCH_LIMIT
) -> List[Book]:
    """
    Search for books using vector similarity and return Book objects.

    Args:
        query_text: Text to search for
        db: Database session
        chromadb_service: ChromaDB client service instance
        limit: Maximum number of results

    Returns:
        List[Book]: List of Book objects
    """
    book_ids = search_by_vector(query_text, chromadb_service, limit)
    if not book_ids:
        return []
    books = db.query(Book).filter(Book.id.in_(book_ids)).all()
    return books
