"""
Vector Database Module for AI Book Seeker

This module handles the vector database operations for storing and retrieving book embeddings.
It uses ChromaDB as the vector store and OpenAI's embeddings for vector generation.
"""

import os
from typing import List

import chromadb
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from ai_book_seeker.core.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIRECTORY, OPENAI_API_KEY
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.models import Book

# Load environment variables
load_dotenv()

# Set up logging
logger = get_logger("vectordb")

# OpenAI client for embeddings
client = OpenAI(api_key=OPENAI_API_KEY)

# Create persistence directory if it doesn't exist
if not os.path.exists(CHROMA_PERSIST_DIRECTORY):
    os.makedirs(CHROMA_PERSIST_DIRECTORY)
    logger.info(f"Created ChromaDB persistence directory: {CHROMA_PERSIST_DIRECTORY}")

# Initialize ChromaDB with persistence
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
logger.info(f"ChromaDB initialized with persistence at: {CHROMA_PERSIST_DIRECTORY}")

# Get or create collection
book_collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
logger.info(f"Using ChromaDB collection: {CHROMA_COLLECTION_NAME}")


def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a text using OpenAI API.

    Args:
        text: The text to embed

    Returns:
        List of embedding values as floats

    Raises:
        ValueError: If OPENAI_EMBEDDING_MODEL environment variable is not set
    """
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
    if not embedding_model:
        logger.error("OPENAI_EMBEDDING_MODEL environment variable is required")
        raise ValueError("OPENAI_EMBEDDING_MODEL environment variable is required")

    response = client.embeddings.create(model=embedding_model, input=text)
    return response.data[0].embedding


def initialize_vector_db(db: Session) -> None:
    """
    Initialize the vector database with book embeddings using batch processing.

    Args:
        db: SQLAlchemy database session
    """
    # Get all books from the database
    books = db.query(Book).all()
    logger.info(f"Initializing vector DB with {len(books)} books")

    # Get existing book IDs in the collection to avoid recreating embeddings
    try:
        existing_ids = set(book_collection.get(include=[])["ids"])
        logger.info(f"Found {len(existing_ids)} existing embeddings in ChromaDB")
    except Exception:
        # If there's an error getting existing IDs, assume none exist
        existing_ids = set()
        logger.info("No existing embeddings found or error accessing ChromaDB")

    # Track counts
    created_count = 0
    skipped_count = 0

    # Batch size for embedding requests
    BATCH_SIZE = 50  # Adjust based on your needs and OpenAI API limits

    # Prepare batches for processing
    books_to_embed = []
    book_ids = []
    book_contents = []

    for book in books:
        book_id = int(book.id)
        book_id_str = f"book-{book_id}"

        # Skip if this book already has an embedding
        if book_id_str in existing_ids:
            skipped_count += 1
            continue

        # Create content to embed
        content_to_embed = f"Title: {book.title} | Description: {book.description} | Age range: {f'{book.from_age}-{book.to_age}' if book.from_age is not None and book.to_age is not None else 'All ages'} | Purpose: {book.purpose} | Genre: {book.genre or 'N/A'} | Tags: {book.tags}"

        books_to_embed.append(book)
        book_ids.append(book_id_str)
        book_contents.append(content_to_embed)

        # Process batch when it reaches BATCH_SIZE
        if len(books_to_embed) >= BATCH_SIZE:
            process_embedding_batch(books_to_embed, book_ids, book_contents)
            created_count += len(books_to_embed)
            books_to_embed = []
            book_ids = []
            book_contents = []

    # Process any remaining books
    if books_to_embed:
        process_embedding_batch(books_to_embed, book_ids, book_contents)
        created_count += len(books_to_embed)

    logger.info(f"Embedding initialization complete: {created_count} created, {skipped_count} skipped")


def process_embedding_batch(books, book_ids, contents):
    """
    Process a batch of books for embedding and storage in ChromaDB.

    Args:
        books: List of Book objects
        book_ids: List of book ID strings
        contents: List of content strings to embed
    """
    try:
        # Get embeddings for the batch
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
        if not embedding_model:
            logger.error("OPENAI_EMBEDDING_MODEL environment variable is required")
            raise ValueError("OPENAI_EMBEDDING_MODEL environment variable is required")

        response = client.embeddings.create(model=embedding_model, input=contents)
        embeddings = [item.embedding for item in response.data]

        # Prepare data for ChromaDB
        embedding_arrays = [np.array(emb, dtype=np.float32) for emb in embeddings]
        metadatas = [{"id": int(book.id), "title": str(book.title)} for book in books]

        # Add to ChromaDB
        book_collection.add(
            embeddings=embedding_arrays,
            documents=contents,
            metadatas=metadatas,
            ids=book_ids,
        )
        logger.debug(f"Added batch of {len(books)} embeddings to ChromaDB")
    except Exception as e:
        logger.error(f"Error creating embeddings batch: {e}")


def search_by_vector(query_text: str, limit: int = 3, threshold: float = 0.7) -> List[int]:
    """
    Search for books using vector similarity.

    Args:
        query_text: The text query to search for
        limit: Maximum number of results to return
        threshold: Similarity threshold for filtering results

    Returns:
        List of book IDs that match the query
    """
    try:
        # Get embedding for query
        query_embedding = get_embedding(query_text)

        # Convert to numpy array for ChromaDB compatibility
        query_embedding_array = np.array(query_embedding, dtype=np.float32)

        # Log search attempt
        logger.debug(f"Searching ChromaDB for query: '{query_text[:50]}...' with limit: {limit}")

        # Search in ChromaDB
        results = book_collection.query(
            query_embeddings=query_embedding_array, n_results=limit, include=["metadatas", "distances"]
        )

        logger.debug(f"ChromaDB search complete, results found: {bool(results and results.get('distances'))}")

        # Extract book IDs from results
        book_ids: List[int] = []

        # Check that all required data exists
        if (
            results
            and "metadatas" in results
            and results["metadatas"]
            and len(results["metadatas"]) > 0
            and "distances" in results
            and results["distances"]
            and len(results["distances"]) > 0
        ):

            distances = results["distances"][0]
            for i, metadata in enumerate(results["metadatas"][0]):
                if i < len(distances) and "id" in metadata:
                    # Convert distance to similarity score (0-1)
                    similarity = 1 - (distances[i] / 2.0)

                    # Only include results above threshold
                    if similarity >= threshold:
                        book_ids.append(int(metadata["id"]))
                        logger.debug(f"Book {metadata['id']}: similarity {similarity:.2f}")
                    else:
                        logger.debug(f"Filtered out book {metadata['id']} with low similarity {similarity:.2f}")

        logger.debug(f"Found {len(book_ids)} similar books for vector query: {query_text[:50]}...")
        return book_ids
    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        return []


def get_book_vector_matches(query_text: str, db: Session, limit: int = 3) -> List[Book]:
    """
    Search for books using vector similarity and return Book objects.

    Args:
        query_text: The search query
        db: SQLAlchemy database session
        limit: Maximum number of results to return

    Returns:
        List of Book objects matching the query
    """
    # Get book IDs from vector search
    book_ids = search_by_vector(query_text, limit)

    if not book_ids:
        return []

    # Fetch the books from the database
    books = db.query(Book).filter(Book.id.in_(book_ids)).all()
    logger.debug(f"Retrieved {len(books)} Book objects from vector search")

    return books
