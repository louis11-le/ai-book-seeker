#!/usr/bin/env python
"""
Utility script to create embeddings for books manually.
This can be used instead of creating embeddings on startup.

Usage:
  python -m scripts.create_embeddings

Environment variables:
  FORCE_RECREATE: Set to "true" to recreate all embeddings even if they exist
"""

import os
import time

from dotenv import load_dotenv

from db.connection import get_db
from db.models import Book
from logger import get_logger, setup_logging
from vectordb import book_collection, initialize_vector_db

# Load environment variables
load_dotenv()


# Configure logging
setup_logging()
logger = get_logger("embedding_script")


def main():
    """Main function to create embeddings"""
    logger.info("Starting manual embedding creation")

    # Check if we should force recreate all embeddings
    force_recreate = os.getenv("FORCE_RECREATE", "True").lower() == "true"

    # Get book count in the database
    db = next(get_db())
    try:
        book_count = db.query(Book).count()
        logger.info(f"Found {book_count} books in the database")

        # Get existing embedding count
        try:
            existing_count = len(book_collection.get(include=[])["ids"])
            logger.info(f"Found {existing_count} existing embeddings in ChromaDB")

            # If force recreate, delete all existing embeddings
            if force_recreate and existing_count > 0:
                logger.info("FORCE_RECREATE=True, deleting all existing embeddings")
                # Get all IDs first, then delete them individually
                all_ids = book_collection.get(include=[])["ids"]
                if all_ids:
                    logger.info(f"Deleting {len(all_ids)} embeddings")
                    book_collection.delete(ids=all_ids)
                    logger.info("Deleted all existing embeddings")
        except Exception as e:
            logger.warning(f"Error checking existing embeddings: {e}")

        # Record start time
        start_time = time.time()

        # Initialize vector DB
        initialize_vector_db(db)

        # Record end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Embedding creation completed in {duration:.2f} seconds")
    finally:
        db.close()

    logger.info("Manual embedding creation finished")


if __name__ == "__main__":
    main()
