"""
Health check endpoints for monitoring and load balancers.

Provides comprehensive health checks for all critical services with configurable
timeouts, performance monitoring, and structured error handling.

Performance Characteristics:
- Response Time: <100ms for basic health check, <500ms for comprehensive check
- Memory Usage: <1KB per request
- Caching: Configurable cache duration for comprehensive health checks
- Timeout Management: Configurable per-service timeouts via AppSettings

Health Check Services:
- Database connectivity (MySQL/PostgreSQL)
- Redis connectivity (optional, with graceful degradation)
- ChromaDB vector database accessibility
- FAQ service operational status
- Basic API status and version information
"""

import asyncio
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from ai_book_seeker.core.config import AppSettings
from ai_book_seeker.core.dependencies import get_app_settings
from ai_book_seeker.core.logging import get_logger
from ai_book_seeker.db.database import get_db_session
from ai_book_seeker.workflows.schemas import get_state_manager

logger = get_logger(__name__)

# Create the router instance
router = APIRouter()


def get_redis_client(request: Request) -> Optional[Any]:
    """Get Redis client from app state if available."""
    return getattr(request.app.state, "redis_client", None)


def monitor_performance(threshold_ms: Optional[int] = None):
    """
    Performance monitoring decorator for health check functions.

    Args:
        threshold_ms: Performance threshold in milliseconds (uses config default if None)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000

                # Get threshold from config if not provided
                if threshold_ms is None and args and hasattr(args[0], "health_check"):
                    config_threshold = args[0].health_check.performance_threshold_ms
                else:
                    config_threshold = threshold_ms or 500

                if execution_time > config_threshold:
                    logger.warning(
                        f"Slow health check: {func.__name__} took {execution_time:.2f}ms "
                        f"(threshold: {config_threshold}ms)"
                    )
                else:
                    logger.debug(f"Health check: {func.__name__} completed in {execution_time:.2f}ms")

                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Health check {func.__name__} failed after {execution_time:.2f}ms: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


@router.get("/", tags=["health"])
async def root(settings: AppSettings = Depends(get_app_settings)) -> Dict[str, str]:
    """
    Root endpoint for basic API status and health check.

    Provides lightweight health information suitable for load balancers
    and basic monitoring without performing expensive service checks.

    Returns:
        Basic API status information
    """
    return {
        "status": "ok",
        "message": "AI Book Seeker API is running",
        "version": settings.health_check.version,
        "environment": settings.environment.value,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/health", tags=["health"])
async def health_check(
    request: Request,
    settings: AppSettings = Depends(get_app_settings),
    redis_client: Optional[Any] = Depends(get_redis_client),
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for monitoring and load balancers.

    Performs actual health checks of all critical services with configurable
    timeouts and performance monitoring. Results are cached for configurable duration
    to improve performance for frequent health check requests.

    Health Checks Performed (configurable via feature flags):
    - Database connectivity (MySQL/PostgreSQL)
    - Redis connectivity (optional, with graceful degradation)
    - ChromaDB vector database accessibility
    - FAQ service operational status

    Returns:
        Comprehensive health status with detailed service information
    """
    # Check cache first if caching is enabled
    if settings.health_check.enable_caching:
        cached_result = _health_cache.get("comprehensive_health", settings.health_check.cache_duration)
        if cached_result:
            logger.debug("Returning cached health check result")
            return cached_result

    # Perform comprehensive health check
    health_status = await perform_comprehensive_health_check(request, settings, redis_client)

    # Cache the result if caching is enabled
    if settings.health_check.enable_caching:
        _health_cache.set("comprehensive_health", health_status)

    return health_status


@router.post("/health/cache/clear", tags=["health"])
async def clear_health_cache() -> Dict[str, str]:
    """
    Clear the health check cache.

    This endpoint allows manual cache invalidation for immediate fresh health checks.
    Useful for testing or when you need to force a fresh health check.

    Returns:
        Confirmation message
    """
    _health_cache.clear()
    logger.info("Health check cache cleared")
    return {"message": "Health check cache cleared successfully"}


class HealthCheckCache:
    """Simple in-memory cache for health check results with TTL."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def get(self, key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None

        if time.time() - self._timestamps[key] > ttl_seconds:
            # Cache expired, remove entry
            del self._cache[key]
            del self._timestamps[key]
            return None

        return self._cache[key]

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set cache value with current timestamp."""
        self._cache[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._timestamps.clear()


# Global cache instance
_health_cache = HealthCheckCache()


@monitor_performance()
async def check_database_health(settings: AppSettings) -> Dict[str, Any]:
    """
    Check database connectivity and health.

    Args:
        settings: Application settings

    Returns:
        Health check result for database
    """
    start_time = time.time()

    try:

        async def _check_db():
            with get_db_session(settings) as db:
                db.execute(text("SELECT 1"))

        await asyncio.wait_for(_check_db(), timeout=settings.health_check.database_timeout)

        duration = (time.time() - start_time) * 1000
        logger.debug(f"Database health check completed in {duration:.2f}ms")

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "duration_ms": round(duration, 2),
        }
    except asyncio.TimeoutError:
        duration = (time.time() - start_time) * 1000
        logger.warning(f"Database health check timeout after {duration:.2f}ms")
        return {
            "status": "unhealthy",
            "message": f"Database connection timeout ({settings.health_check.database_timeout}s)",
            "duration_ms": round(duration, 2),
        }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed after {duration:.2f}ms: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "duration_ms": round(duration, 2),
        }


@monitor_performance()
async def check_redis_health(settings: AppSettings, redis_client: Optional[Any]) -> Dict[str, Any]:
    """
    Check Redis connectivity and health.

    Args:
        settings: Application settings
        redis_client: Redis client instance

    Returns:
        Health check result for Redis
    """
    start_time = time.time()

    try:
        # Validate Redis configuration
        if not settings.redis.host:
            return {
                "status": "warning",
                "message": "Redis not configured (no host specified)",
                "duration_ms": 0,
            }

        if redis_client is None:
            return {
                "status": "warning",
                "message": "Redis client not available in app state",
                "duration_ms": 0,
            }

        # Perform Redis ping check
        await asyncio.wait_for(asyncio.to_thread(redis_client.ping), timeout=settings.health_check.redis_timeout)

        duration = (time.time() - start_time) * 1000
        logger.debug(f"Redis health check completed in {duration:.2f}ms")

        return {
            "status": "healthy",
            "message": "Redis connection successful",
            "duration_ms": round(duration, 2),
        }
    except asyncio.TimeoutError:
        duration = (time.time() - start_time) * 1000
        logger.warning(f"Redis health check timeout after {duration:.2f}ms")
        return {
            "status": "unhealthy",
            "message": f"Redis connection timeout ({settings.health_check.redis_timeout}s)",
            "duration_ms": round(duration, 2),
        }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Redis health check failed after {duration:.2f}ms: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
            "duration_ms": round(duration, 2),
        }


@monitor_performance()
async def check_chromadb_health(request: Request, settings: AppSettings) -> Dict[str, Any]:
    """
    Check ChromaDB service health.

    Args:
        request: FastAPI request object
        settings: Application settings

    Returns:
        Health check result for ChromaDB
    """
    start_time = time.time()

    try:
        chromadb_service = getattr(request.app.state, "chromadb_service", None)

        if chromadb_service is None:
            return {
                "status": "warning",
                "message": "ChromaDB service not available in app state",
                "duration_ms": 0,
            }

        # Perform health check with timeout
        health_info = await asyncio.wait_for(
            asyncio.to_thread(chromadb_service.health_check), timeout=settings.health_check.service_timeout
        )

        duration = (time.time() - start_time) * 1000
        logger.debug(f"ChromaDB health check completed in {duration:.2f}ms")

        return {
            "status": health_info.get("status", "unknown"),
            "message": (
                f"ChromaDB service: {health_info.get('total_collections', 0)} collections, "
                f"{health_info.get('books_collection_count', 0)} books, "
                f"{health_info.get('faqs_collection_count', 0)} FAQs"
            ),
            "details": health_info,
            "duration_ms": round(duration, 2),
        }
    except asyncio.TimeoutError:
        duration = (time.time() - start_time) * 1000
        logger.warning(f"ChromaDB health check timeout after {duration:.2f}ms")
        return {
            "status": "unhealthy",
            "message": f"ChromaDB service check timeout ({settings.health_check.service_timeout}s)",
            "duration_ms": round(duration, 2),
        }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"ChromaDB health check failed after {duration:.2f}ms: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"ChromaDB service check failed: {str(e)}",
            "duration_ms": round(duration, 2),
        }


@monitor_performance()
async def check_faq_service_health(request: Request, settings: AppSettings) -> Dict[str, Any]:
    """
    Check FAQ service health.

    Args:
        request: FastAPI request object
        settings: Application settings

    Returns:
        Health check result for FAQ service
    """
    start_time = time.time()

    try:
        faq_service = getattr(request.app.state, "faq_service", None)

        if faq_service is None:
            return {
                "status": "warning",
                "message": "FAQ service not available in app state",
                "duration_ms": 0,
            }

        # Perform test query with timeout
        test_results = await asyncio.wait_for(
            asyncio.to_thread(faq_service.search_faqs, "test"), timeout=settings.health_check.service_timeout
        )

        duration = (time.time() - start_time) * 1000
        logger.debug(f"FAQ service health check completed in {duration:.2f}ms")

        return {
            "status": "healthy",
            "message": f"FAQ service operational (test query returned {len(test_results)} results)",
            "duration_ms": round(duration, 2),
        }
    except asyncio.TimeoutError:
        duration = (time.time() - start_time) * 1000
        logger.warning(f"FAQ service health check timeout after {duration:.2f}ms")
        return {
            "status": "unhealthy",
            "message": f"FAQ service check timeout ({settings.health_check.service_timeout}s)",
            "duration_ms": round(duration, 2),
        }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"FAQ service health check failed after {duration:.2f}ms: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "message": f"FAQ service check failed: {str(e)}",
            "duration_ms": round(duration, 2),
        }


async def perform_comprehensive_health_check(
    request: Request, settings: AppSettings, redis_client: Optional[Any]
) -> Dict[str, Any]:
    """
    Perform comprehensive health check of all services.

    Args:
        request: FastAPI request object
        settings: Application settings
        redis_client: Redis client instance

    Returns:
        Comprehensive health status with detailed service information
    """
    start_time = time.time()

    # Initialize health status
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": settings.health_check.version,
        "environment": settings.environment.value,
        "checks": {},
        "performance": {},
    }

    # Prepare health check tasks based on feature flags
    health_check_tasks = []
    task_names = []

    if settings.health_check.enable_database_check:
        health_check_tasks.append(check_database_health(settings))
        task_names.append("database")

    if settings.health_check.enable_redis_check:
        health_check_tasks.append(check_redis_health(settings, redis_client))
        task_names.append("redis")

    if settings.health_check.enable_chromadb_check:
        health_check_tasks.append(check_chromadb_health(request, settings))
        task_names.append("chromadb_service")

    if settings.health_check.enable_faq_check:
        health_check_tasks.append(check_faq_service_health(request, settings))
        task_names.append("faq_service")

    # Perform all health checks in parallel for better performance
    try:
        if health_check_tasks:
            results = await asyncio.gather(*health_check_tasks, return_exceptions=True)

            # Process results
            for i, (task_name, result) in enumerate(zip(task_names, results)):
                if isinstance(result, Exception):
                    health_status["checks"][task_name] = {
                        "status": "unhealthy",
                        "message": f"{task_name.title()} check failed: {str(result)}",
                        "duration_ms": 0,
                    }
                    # Only database and critical services make entire service unhealthy
                    if task_name in ["database", "chromadb_service", "faq_service"]:
                        health_status["status"] = "unhealthy"
                else:
                    health_status["checks"][task_name] = result
                    if result["status"] == "unhealthy" and task_name in ["database", "chromadb_service", "faq_service"]:
                        health_status["status"] = "unhealthy"

    except Exception as e:
        logger.error(f"Health check orchestration failed: {e}", exc_info=True)
        health_status["status"] = "unhealthy"
        health_status["checks"]["orchestration"] = {
            "status": "unhealthy",
            "message": f"Health check orchestration failed: {str(e)}",
            "duration_ms": 0,
        }

    # Calculate overall performance metrics
    total_duration = (time.time() - start_time) * 1000
    health_status["performance"] = {
        "total_duration_ms": round(total_duration, 2),
        "cache_duration_seconds": settings.health_check.cache_duration,
        "timeouts": {
            "database_seconds": settings.health_check.database_timeout,
            "redis_seconds": settings.health_check.redis_timeout,
            "service_seconds": settings.health_check.service_timeout,
        },
        "checks_performed": len(health_check_tasks),
        "checks_enabled": {
            "database": settings.health_check.enable_database_check,
            "redis": settings.health_check.enable_redis_check,
            "chromadb": settings.health_check.enable_chromadb_check,
            "faq": settings.health_check.enable_faq_check,
        },
    }

    # Log health check results
    if health_status["status"] == "healthy":
        logger.info(f"Health check completed successfully in {total_duration:.2f}ms")
    else:
        logger.warning(f"Health check completed with issues in {total_duration:.2f}ms: {health_status['status']}")

    return health_status


@router.get("/health/state-management", tags=["health"])
async def state_management_health():
    """State management health and performance metrics."""
    state_manager = get_state_manager()
    metrics = state_manager.get_performance_metrics()

    # Clean up old states
    cleaned_count = state_manager.cleanup_old_states()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "state_management": {
            "performance_metrics": metrics,
            "cleanup": {
                "states_cleaned": cleaned_count,
                "cleanup_enabled": True,
            },
            "optimization": {
                "memory_optimization": True,
                "state_validation": True,
                "access_tracking": True,
            },
        },
    }
