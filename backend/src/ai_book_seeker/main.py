"""
AI Book Seeker - Main application entry point

This module initializes the FastAPI application with proper configuration,
middleware, and startup/shutdown lifecycle management following best practices.

Configuration Pattern:
- Single source of truth: app.state.config
- All services receive settings as parameters
- No global singleton pattern
- Clean dependency injection for testing
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_openai import OpenAIEmbeddings

from .api.routes import register_routers
from .core.config import AppSettings, create_settings
from .core.logging import get_logger, setup_logging
from .db.database import get_db_session
from .features.search_faq.faq_service import FAQService
from .services.redis_client import create_redis_client
from .services.vectordb import create_book_embeddings_from_database
from .utils.chromadb_service import ChromaDBService

# Initialize logger
logger = get_logger(__name__)


class StartupError(Exception):
    """Custom exception for startup-related errors."""

    pass


class ServiceInitializationError(Exception):
    """Custom exception for service initialization errors."""

    pass


async def startup_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for startup errors.

    Args:
        request: The incoming request
        exc: The startup exception

    Returns:
        JSONResponse: Error response with appropriate status code
    """
    logger.error(f"Startup error occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": "Service temporarily unavailable",
            "detail": "The application is still starting up. Please try again later.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


async def service_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for service initialization errors.

    Args:
        request: The incoming request
        exc: The service initialization exception

    Returns:
        JSONResponse: Error response with appropriate status code
    """
    logger.error(f"Service initialization error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={
            "error": "Service initialization failed",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        JSONResponse: Error response with appropriate status code
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


async def validate_configuration(settings: AppSettings) -> None:
    """
    Validate that all required configuration is properly set.

    Args:
        settings: The application settings to validate

    Raises:
        ServiceInitializationError: If required configuration is missing or invalid
    """
    try:
        # Validate OpenAI configuration
        if not settings.openai.api_key.get_secret_value():
            raise ServiceInitializationError("OpenAI API key is required but not configured")

        # Validate database configuration
        if not settings.database.url and not settings.database.host:
            raise ServiceInitializationError("Database configuration is required but not properly configured")

        # Validate ChromaDB configuration
        if not settings.chromadb.book_persist_directory:
            raise ServiceInitializationError("ChromaDB book persist directory is required but not configured")

        if not settings.chromadb.faq_persist_directory:
            raise ServiceInitializationError("ChromaDB FAQ persist directory is required but not configured")

        # Validate knowledge base path exists
        if not os.path.exists(settings.knowledge_base_path):
            logger.warning(f"Knowledge base path does not exist: {settings.knowledge_base_path}")
            # Don't fail startup for this - it's a warning

        logger.info("Configuration validation completed successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}", exc_info=True)
        raise ServiceInitializationError(f"Configuration validation failed: {e}") from e


async def initialize_configuration(app: FastAPI) -> AppSettings:
    """
    Initialize and attach configuration to app state.

    Args:
        app: FastAPI application instance

    Returns:
        AppSettings: The initialized settings instance
    """
    try:
        # Create settings instance using the factory function
        settings = create_settings()

        # Validate configuration before proceeding
        await validate_configuration(settings)

        app.state.config = settings
        logger.info("Configuration initialized and attached to app state")
        return settings
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}", exc_info=True)
        raise ServiceInitializationError(f"Configuration initialization failed: {e}") from e


async def initialize_faq_service(app: FastAPI, settings: AppSettings) -> None:
    """
    Initialize FAQ service and attach to app state.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    try:
        kb_dir = settings.knowledge_base_path
        chromadb_service = app.state.chromadb_service
        app.state.faq_service = await FAQService.async_init(kb_dir, settings, chromadb_service)
        logger.info("FAQService initialized and stored in app.state")
    except Exception as e:
        logger.error(f"Failed to initialize FAQ service: {e}", exc_info=True)
        raise ServiceInitializationError(f"FAQ service initialization failed: {e}") from e


async def initialize_redis_client(app: FastAPI, settings: AppSettings) -> None:
    """
    Initialize Redis client and attach to app state.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    try:
        app.state.redis_client = create_redis_client(settings)
        logger.info("Redis client initialized and stored in app.state")
    except Exception as e:
        logger.error(f"Failed to initialize Redis client: {e}", exc_info=True)
        raise ServiceInitializationError(f"Redis client initialization failed: {e}") from e


async def initialize_chromadb_service(app: FastAPI, settings: AppSettings) -> None:
    """
    Initialize ChromaDB service and attach to app state.

    This function creates the ChromaDB service with proper embedding provider
    configuration and stores it in the application state for dependency injection.

    Args:
        app: FastAPI application instance
        settings: Application settings

    Raises:
        ServiceInitializationError: If ChromaDB service initialization fails
    """
    try:
        # Create embedding provider
        embedding_model = getattr(settings.openai, "embedding_model", settings.openai.model)
        embedding_provider = OpenAIEmbeddings(model=embedding_model)

        app.state.chromadb_service = ChromaDBService(
            settings=settings,
            embedding_provider=embedding_provider,
        )
        logger.info("ChromaDB service initialized and stored in app.state")
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB service: {e}", exc_info=True)
        raise ServiceInitializationError(f"ChromaDB service initialization failed: {e}") from e


async def populate_book_embeddings(app: FastAPI, settings: AppSettings) -> None:
    """
    Populate the vector database with book embeddings from the database.

    This function loads books from the database and creates embeddings for them
    in the ChromaDB vector store. This is a separate operation from service initialization
    and can be skipped for faster startup or when embeddings are pre-loaded.
    """
    if settings.startup.skip_vector_init:
        logger.info("Skipping book embeddings population (STARTUP_SKIP_VECTOR_INIT=True)")
        return

    try:
        with get_db_session(settings) as db:
            create_book_embeddings_from_database(db, app.state.chromadb_service)
            logger.info("Book embeddings population completed")
    except Exception as e:
        logger.error(f"Failed to populate book embeddings: {e}", exc_info=True)
        # Don't fail startup for embedding population - log and continue
        logger.warning("Continuing startup without book embeddings population")


async def cleanup_resources() -> None:
    """
    Clean up application resources during shutdown.

    This function handles graceful cleanup of any resources
    that need explicit cleanup (file handles, connections, etc.).
    """
    try:
        # Add any cleanup logic for services if needed
        # Currently no explicit cleanup is required for the services
        logger.info("Resource cleanup complete")
    except Exception as e:
        logger.error(f"Error during resource cleanup: {e}", exc_info=True)
        # Don't raise during shutdown - just log the error


async def startup_application(app: FastAPI) -> None:
    """
    Perform all application startup operations.

    This function orchestrates the startup sequence:
    1. Initialize configuration
    2. Setup logging (using configuration)
    3. Initialize ChromaDB service (required by other services)
    4. Populate book embeddings (optional, can be skipped)
    5. Initialize other services in parallel (Redis, FAQ)

    Args:
        app: FastAPI application instance
    """
    logger.info("Starting AI Book Seeker API")

    try:
        # Initialize configuration first (required by other services)
        settings = await initialize_configuration(app)

        # Setup logging with configuration (must be done early)
        setup_logging(
            log_level=settings.logging.level,
            environment=settings.environment.value,
            enable_file_logging=settings.logging.enable_file_logging,
            log_directory=settings.logging.log_directory,
            log_filename=settings.logging.log_filename,
            error_log_filename=settings.logging.error_log_filename,
            max_file_size_mb=settings.logging.max_file_size_mb,
            backup_count=settings.logging.backup_count,
            enable_console_logging=settings.logging.enable_console_logging,
        )
        logger.info(f"Logging configured with level: {settings.logging.level}")
        if settings.logging.enable_file_logging:
            logger.info(f"File logging enabled: {settings.logging.log_directory}/{settings.logging.log_filename}")

        # Initialize ChromaDB service first (required by other services)
        await initialize_chromadb_service(app, settings)

        # Populate book embeddings (can be skipped for faster startup)
        await populate_book_embeddings(app, settings)

        # Initialize other services in parallel
        await asyncio.gather(
            initialize_redis_client(app, settings),
            initialize_faq_service(app, settings),
            return_exceptions=True,  # Continue startup even if individual services fail
        )

        logger.info("AI Book Seeker API startup complete")
    except Exception as e:
        logger.error(f"Application startup failed: {e}", exc_info=True)
        raise StartupError(f"Application startup failed: {e}") from e


async def shutdown_application() -> None:
    """
    Perform all application shutdown operations.

    This function orchestrates the shutdown sequence:
    1. Clean up resources
    2. Log shutdown completion
    """
    logger.info("Shutting down AI Book Seeker API")

    try:
        await cleanup_resources()
        logger.info("AI Book Seeker API shutdown complete")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)
        # Don't raise during shutdown - just log the error


def create_app(settings: Optional[AppSettings] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function follows best practices for
    application configuration and dependency injection.

    Args:
        settings: Application settings. If None, will call create_settings().
                 This parameter allows for dependency injection and testing.
    """
    # Get settings if not provided (allows for dependency injection and testing)
    if settings is None:
        settings = create_settings()

    # Create FastAPI application with metadata
    app = FastAPI(
        title="AI Book Seeker",
        description="AI-powered book recommendation system with natural language understanding",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # Register global exception handlers
    app.add_exception_handler(StartupError, startup_exception_handler)
    app.add_exception_handler(ServiceInitializationError, service_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Configure CORS middleware with environment-specific settings
    cors_origins = ["*"] if settings.is_development else settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Automatically discover and register all API routers
    register_routers(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    This follows the modern FastAPI pattern for resource management,
    replacing the deprecated @app.on_event decorators.

    The lifespan function is now a thin orchestrator that delegates
    to focused, testable functions for each phase of the lifecycle.

    Args:
        app: FastAPI application instance
    """
    # Startup phase
    await startup_application(app)

    yield

    # Shutdown phase
    await shutdown_application()


# Dependency injection functions for accessing app state
def get_faq_service(request: Request) -> "FAQService":
    """
    Dependency to get FAQ service from app state.

    Args:
        request: The FastAPI request object

    Returns:
        FAQService: The FAQ service instance

    Raises:
        RuntimeError: If FAQ service is not available in app state
    """
    if not hasattr(request.app.state, "faq_service"):
        raise RuntimeError("FAQ service not available in app state")
    return request.app.state.faq_service


def get_redis_client(request: Request) -> Any:
    """
    Dependency to get Redis client from app state.

    Args:
        request: The FastAPI request object

    Returns:
        redis.Redis: The Redis client instance

    Raises:
        RuntimeError: If Redis client is not available in app state
    """
    if not hasattr(request.app.state, "redis_client"):
        raise RuntimeError("Redis client not available in app state")
    return request.app.state.redis_client


def get_chromadb_service(request: Request) -> "ChromaDBService":
    """
    Dependency to get ChromaDB service from app state.

    Args:
        request: The FastAPI request object

    Returns:
        ChromaDBService: The ChromaDB service instance

    Raises:
        RuntimeError: If ChromaDB service is not available in app state
    """
    if not hasattr(request.app.state, "chromadb_service"):
        raise RuntimeError("ChromaDB service not available in app state")
    return request.app.state.chromadb_service


# Create the application instance
app = create_app()


if __name__ == "__main__":
    logger.info("Starting AI Book Seeker API in standalone mode")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
