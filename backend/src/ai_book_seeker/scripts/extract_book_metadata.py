#!/usr/bin/env python
"""
CLI Script for Book Metadata Extraction

This script provides a command-line interface for extracting metadata from
PDF book files and saving it to the database.
"""

import argparse
import json
import sys

from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction import extract_book_metadata

# Set up logging
logger = get_logger("extract_book_metadata_cli")


def main():
    """Main function for the CLI script."""
    parser = argparse.ArgumentParser(description="Extract metadata from a PDF book file")
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF book file",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Don't save the metadata to the database",
    )
    parser.add_argument(
        "--output",
        help="Path to save the extracted metadata as JSON",
    )
    args = parser.parse_args()

    try:
        # Extract metadata
        metadata = extract_book_metadata(
            args.pdf_path,
            save_to_db=not args.no_db,
            output_path=args.output,
        )

        if not metadata:
            logger.error("Failed to extract metadata")
            sys.exit(1)

        # Print metadata to stdout
        print(json.dumps(metadata, indent=2))

        # Save to JSON file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved to {args.output}")

        logger.info("Metadata extraction complete")
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
