"""
AI Book Seeker Backend API

This module serves as the main entry point for the FastAPI application.
It handles HTTP requests, initializes resources, and provides the core API
endpoints for book recommendations through natural language conversation.

The API provides endpoints for:
- Health check
- Chat functionality for book recommendations
- Session management
"""

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from chat_parser import ChatRequest, ChatResponse, process_chat_request
from db.connection import Base, engine, get_db
from logger import get_logger, setup_logging
from memory import SessionMemory
from vectordb import initialize_vector_db

# Load environment variables
load_dotenv()

# Configure logging
setup_logging()
logger = get_logger("main")

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Book Seeker",
    description="AI-powered book recommendation assistant",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production specify allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("Starting AI Book Seeker API")

    # Check if we should skip vector DB initialization
    skip_vector_init = os.getenv("SKIP_VECTOR_INIT", "False").lower() == "true"
    if skip_vector_init:
        logger.info("Skipping vector database initialization (SKIP_VECTOR_INIT=True)")
        return

    # Get a database session
    db = next(get_db())
    try:
        # Initialize the vector database
        initialize_vector_db(db)
        logger.info("Vector database initialized successfully")
    finally:
        db.close()


# API routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Book Seeker API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for book recommendations"""
    try:
        # Process the chat request
        response = process_chat_request(request)
        return response
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        SessionMemory.delete_session(session_id)
        logger.info(f"Session {session_id} deleted successfully")
        return {"status": "ok", "message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


# Main entry point
if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    logger.info(f"Starting server at http://{host}:{port}")

    # Use the local module path
    uvicorn.run("main:app", host=host, port=port, reload=debug)
