"""
Automatic router discovery and registration for the AI Book Seeker API.

This module provides a centralized way to discover and register all API routers


Features:
- Configuration-driven router discovery
- Pydantic validation for router configuration
- Environment-specific router loading
- Comprehensive error handling and logging
- Type-safe router registration
"""

import importlib
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from ai_book_seeker.core.logging import get_logger

logger = get_logger(__name__)


class RouterConfig(BaseModel):
    """
    Pydantic model for router configuration validation.

    Ensures type safety and validation for router configuration,
    following best practices for configuration management.
    """

    module: str = Field(..., description="Python module path containing the router")
    router_name: str = Field(..., description="Name of the router variable in the module")
    prefix: str = Field(default="/api", description="URL prefix for the router")
    tags: List[str] = Field(default_factory=list, description="OpenAPI tags for documentation")
    description: str = Field(..., description="Human-readable description of the router")
    enabled: bool = Field(default=True, description="Whether the router should be loaded")
    dependencies: Optional[List[str]] = Field(
        default=None, description="Optional list of dependency modules that must be available"
    )

    @field_validator("module")
    @classmethod
    def validate_module_path(cls, v: str) -> str:
        """Validate that the module path is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Module path cannot be empty")
        if not v.replace(".", "").replace("_", "").isalnum():
            raise ValueError("Module path contains invalid characters")
        return v.strip()

    @field_validator("router_name")
    @classmethod
    def validate_router_name(cls, v: str) -> str:
        """Validate that the router name is properly formatted."""
        if not v or not v.strip():
            raise ValueError("Router name cannot be empty")
        if not v.replace("_", "").isalnum():
            raise ValueError("Router name contains invalid characters")
        return v.strip()

    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """Validate that the prefix starts with a forward slash or is empty for root routes."""
        if v and not v.startswith("/"):
            raise ValueError("Prefix must start with a forward slash or be empty for root routes")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate that tags are non-empty strings."""
        if not v:
            return v
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tags cannot be empty")
        return [tag.strip() for tag in v]


class RouterRegistry:
    """
    Registry for managing router configurations and discovery.

    Provides a centralized way to manage router configurations
    with validation and environment-specific loading.
    """

    def __init__(self):
        self._configs: Dict[str, RouterConfig] = {}
        self._loaded_routers: Dict[str, Tuple[APIRouter, RouterConfig]] = {}

    def register_config(self, name: str, config: RouterConfig) -> None:
        """
        Register a router configuration.

        Args:
            name: Unique name for the router
            config: Validated router configuration
        """
        self._configs[name] = config
        logger.debug(f"Registered router config: {name}")

    def get_config(self, name: str) -> Optional[RouterConfig]:
        """Get a router configuration by name."""
        return self._configs.get(name)

    def get_all_configs(self) -> Dict[str, RouterConfig]:
        """Get all registered router configurations."""
        return self._configs.copy()

    def discover_routers(self) -> List[Tuple[str, APIRouter, RouterConfig]]:
        """
        Automatically discover and load all enabled configured routers.

        Returns:
            List of tuples containing (router_name, router_instance, config)
        """
        routers = []

        for router_name, config in self._configs.items():
            if not config.enabled:
                logger.debug(f"Skipping disabled router: {router_name}")
                continue

            try:
                # Check dependencies if specified
                if config.dependencies:
                    for dep in config.dependencies:
                        try:
                            importlib.import_module(dep)
                        except ImportError as e:
                            logger.warning(f"Dependency {dep} not available for router {router_name}: {e}")
                            continue

                # Import the module
                module = importlib.import_module(config.module)

                # Get the router instance
                router = getattr(module, config.router_name)

                # Validate it's an APIRouter
                if not isinstance(router, APIRouter):
                    logger.warning(f"Router {router_name} is not an APIRouter instance")
                    continue

                routers.append((router_name, router, config))
                self._loaded_routers[router_name] = (router, config)
                logger.debug(f"Discovered router: {router_name} from {config.module}")

            except ImportError as e:
                logger.warning(f"Could not import router {router_name} from {config.module}: {e}")
            except AttributeError as e:
                logger.warning(f"Could not find router {config.router_name} in {config.module}: {e}")
            except Exception as e:
                logger.error(f"Error discovering router {router_name}: {e}", exc_info=True)

        return routers

    def get_loaded_routers(self) -> Dict[str, Tuple[APIRouter, RouterConfig]]:
        """Get all successfully loaded routers."""
        return self._loaded_routers.copy()


# Global router registry instance
router_registry = RouterRegistry()


# Define router configuration with Pydantic validation
ROUTER_CONFIGS = {
    "health": RouterConfig(
        module="ai_book_seeker.api.routes.health",
        router_name="router",
        prefix="",  # Root prefix for health endpoints (no prefix needed)
        tags=["health"],
        description="Health check endpoints for monitoring and load balancers",
        enabled=True,
    ),
    "chat": RouterConfig(
        module="ai_book_seeker.api.routes.chat",
        router_name="router",
        prefix="/api",
        tags=["chat"],
        description="Chat interface endpoints for streaming conversations",
        enabled=True,
    ),
    "session": RouterConfig(
        module="ai_book_seeker.api.routes.session",
        router_name="router",
        prefix="/api",
        tags=["session"],
        description="Session management endpoints for user sessions",
        enabled=True,
    ),
    "voice_assistant": RouterConfig(
        module="ai_book_seeker.api.routes.voice_assistant",
        router_name="router",
        prefix="/api",
        tags=["voice"],
        description="Voice assistant endpoints for ElevenLabs integration",
        enabled=True,
    ),
    "metadata": RouterConfig(
        module="ai_book_seeker.metadata_extraction",
        router_name="metadata_router",
        prefix="/api",
        tags=["metadata"],
        description="Metadata extraction endpoints for PDF processing",
        enabled=True,
    ),
}


def initialize_router_registry() -> None:
    """
    Initialize the router registry with all configured routers.

    This function should be called during application startup
    to populate the registry with all available router configurations.
    """
    for name, config in ROUTER_CONFIGS.items():
        router_registry.register_config(name, config)

    logger.info(f"Initialized router registry with {len(ROUTER_CONFIGS)} configurations")


def discover_routers() -> List[Tuple[str, APIRouter, RouterConfig]]:
    """
    Automatically discover and load all configured routers.

    Returns:
        List of tuples containing (router_name, router_instance, config)
    """
    return router_registry.discover_routers()


def register_routers(app) -> None:
    """
    Automatically register all discovered routers with the FastAPI app.

    This function follows best practices for modular router registration
    by using configuration-driven discovery with Pydantic validation.

    Args:
        app: FastAPI application instance
    """
    routers = discover_routers()

    for router_name, router, config in routers:
        try:
            app.include_router(router, prefix=config.prefix, tags=config.tags)
            logger.info(f"Registered router: {router_name} with prefix: {config.prefix}")
        except Exception as e:
            logger.error(f"Failed to register router {router_name}: {e}", exc_info=True)
            raise


def get_router_info() -> Dict[str, Dict]:
    """
    Get information about all configured routers for documentation and debugging.

    Returns:
        Dictionary mapping router names to their configuration
    """
    configs = router_registry.get_all_configs()
    return {
        name: {
            "module": config.module,
            "router_name": config.router_name,
            "prefix": config.prefix,
            "tags": config.tags,
            "description": config.description,
            "enabled": config.enabled,
            "dependencies": config.dependencies,
        }
        for name, config in configs.items()
    }


def get_router_status() -> Dict[str, Dict]:
    """
    Get the status of all routers including loading state.

    Returns:
        Dictionary with router status information
    """
    configs = router_registry.get_all_configs()
    loaded_routers = router_registry.get_loaded_routers()

    status = {}
    for name, config in configs.items():
        is_loaded = name in loaded_routers
        status[name] = {
            "enabled": config.enabled,
            "loaded": is_loaded,
            "module": config.module,
            "description": config.description,
        }

    return status


# Initialize the registry when the module is imported
initialize_router_registry()
