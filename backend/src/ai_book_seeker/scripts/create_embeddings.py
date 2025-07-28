#!/usr/bin/env python
"""
Utility script to create embeddings for books manually.
This can be used instead of creating embeddings on startup.

Usage:
  python -m scripts.create_embeddings

Configuration:
  All configuration is accessed via AppSettings (see core/config.py).
  - FORCE_RECREATE flag is set via settings.scripts.force_recreate (from .env or environment variable SCRIPTS_FORCE_RECREATE).

Note: This functionality is also available during application startup via the populate_book_embeddings function.
"""

import time

from ai_book_seeker.core.config import create_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.db.models import Book
from ai_book_seeker.services.vectordb import create_book_embeddings_from_database
from ai_book_seeker.utils.chromadb_service import ChromaDBService
from langchain_openai import OpenAIEmbeddings

# Configure logging
logger = get_logger("embedding_script")

# Load settings (centralized config)
settings = create_settings()


def main():
    """Main function to create embeddings"""
    logger.info("Starting manual embedding creation")

    # Validate required settings
    if not settings.openai.api_key.get_secret_value():
        logger.error("OpenAI API key is required but not configured")
        return

    # Create embedding provider using centralized configuration
    embedding_provider = OpenAIEmbeddings(model=settings.openai.embedding_model)

    # Create ChromaDB service
    chromadb_service = ChromaDBService(
        settings=settings,
        embedding_provider=embedding_provider,
    )

    # Use configuration flags
    force_recreate = settings.scripts.force_recreate
    batch_size = settings.scripts.batch_size
    logger.info(f"FORCE_RECREATE flag from config: {force_recreate}")
    logger.info(f"Batch size from config: {batch_size}")

    try:
        # Get book count in the database
        with get_db_session(settings) as db:
            book_count = db.query(Book).count()
            logger.info(f"Found {book_count} books in the database")

            if book_count == 0:
                logger.warning("No books found in database. Skipping embedding creation.")
                return

            # Get existing embedding count and handle force recreate
            try:
                book_collection = chromadb_service.get_books_collection()
                collection_data = book_collection.get(include=[])
                existing_ids = collection_data["ids"]
                existing_count = len(existing_ids)
                logger.info(f"Found {existing_count} existing embeddings in ChromaDB")

                # If force recreate, delete all existing embeddings
                if force_recreate and existing_count > 0:
                    logger.info("FORCE_RECREATE=True, deleting all existing embeddings")
                    logger.info(f"Deleting {existing_count} embeddings")
                    book_collection.delete(ids=existing_ids)
                    logger.info("Deleted all existing embeddings")
            except Exception as e:
                logger.warning(f"Error checking existing embeddings: {e}")
                # Continue with embedding creation even if checking fails

            # Record start time
            start_time = time.time()

            # Create book embeddings from database records
            create_book_embeddings_from_database(db, chromadb_service)

            # Record end time and calculate duration
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Embedding creation completed in {duration:.2f} seconds")

        logger.info("Manual embedding creation finished")

    except Exception as e:
        logger.error(f"Failed to create embeddings: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
