"""
AI Book Seeker - Main application entry point
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.logging import get_logger
from .db.database import get_db_session
from .metadata_extraction import metadata_router
from .services.vectordb import initialize_vector_db

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(title="AI Book Seeker", version="0.1.0")

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(api_router, prefix="/api")

# Include metadata extraction routes
app.include_router(metadata_router, prefix="/api")


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

    # Get a database session using context manager
    with get_db_session() as db:
        # Initialize the vector database
        initialize_vector_db(db)
        logger.info("Vector database initialized successfully")


@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"status": "ok", "message": "AI Book Seeker API is running"}


if __name__ == "__main__":
    logger.info("Starting AI Book Seeker API")
    uvicorn.run(app, host="0.0.0.0", port=8000)
