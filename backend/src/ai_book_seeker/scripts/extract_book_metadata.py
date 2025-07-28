#!/usr/bin/env python
"""
CLI Script for Book Metadata Extraction

This script provides a command-line interface for extracting metadata from
PDF book files and saving it to the database.

All configuration (output directory, file naming, feature flags) is accessed via the centralized AppSettings config object.
Do not use direct environment variable access or hardcoded values; use only AppSettings.
To override config for testing or different environments, set environment variables or edit your .env file.
"""

import argparse
import json
import sys

from ai_book_seeker.core.config import create_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.metadata_extraction import extract_book_metadata

# Set up logging
logger = get_logger("extract_book_metadata_cli")
# Load settings (centralized config, for future-proofing)
settings = create_settings()


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
        # Extract metadata (all config is handled via AppSettings)
        metadata = extract_book_metadata(
            args.pdf_path,
            settings,
            save_to_db=not args.no_db,
            output_path=args.output,
        )

        if not metadata:
            logger.error("Failed to extract metadata")
            sys.exit(1)

        # Print metadata to stdout
        if args.output:
            with open(args.output, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved to {args.output}")
        else:
            logger.info("Metadata extraction complete")

    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
