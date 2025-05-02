"""
Configuration settings for the AI Book Seeker application.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# Database settings
DATABASE_URL = os.getenv("MYSQL_CONNECTION_STRING")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_EXPIRE_SECONDS = int(os.getenv("REDIS_EXPIRE_SECONDS", "7200"))  # 2 hours default

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "200"))
OPENAI_PDF_READER_MODEL = os.getenv("OPENAI_PDF_READER_MODEL", OPENAI_MODEL)  # Default to main model if not specified

# Batch processing settings
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))

# ChromaDB settings
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", str(BACKEND_DIR / "chromadb_data"))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "books")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
