"""
Centralized configuration for the AI Book Seeker application using Pydantic Settings.
All configuration is loaded from environment variables or .env file, with safe defaults for development.
Access config via create_settings(), not os.environ or global constants.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories for robust path construction
# Calculate paths relative to the config file location for consistency
CONFIG_FILE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CONFIG_FILE_DIR.parent.parent.parent  # ai_book_seeker/core -> ai_book_seeker -> src -> backend
BASE_DIR = BACKEND_DIR.parent  # backend -> project_root


class Environment(str, Enum):
    """Environment types for conditional configuration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class RedisSettings(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: Optional[SecretStr] = Field(default=None)
    db: int = Field(default=0)
    expire_seconds: int = Field(default=3600)  # 1 hour default TTL

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class DatabaseSettings(BaseSettings):
    url: Optional[str] = Field(
        default=None, description="Database connection URL (overrides individual fields if provided)"
    )
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=3306, description="Database port")
    username: str = Field(default="root", description="Database username")
    password: SecretStr = Field(default_factory=lambda: SecretStr(""), description="Database password")
    database: str = Field(default="ai_book_seeker", description="Database name")
    echo_sql: bool = Field(default=False, description="Echo SQL queries (for debugging)")

    model_config = SettingsConfigDict(env_prefix="DB_")

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format if provided."""
        if v is not None:
            # Basic URL validation - ensure it starts with a valid database scheme
            valid_schemes = [
                "mysql",
                "mysql+pymysql",
                "mysql+mysqlconnector",
                "postgresql",
                "postgresql+psycopg2",
                "sqlite",
            ]
            if not any(v.startswith(f"{scheme}://") for scheme in valid_schemes):
                raise ValueError(f"Invalid database URL scheme. Must start with one of: {valid_schemes}")
        return v

    def get_connection_url(self) -> str:
        """
        Get the database connection URL.

        If a URL is explicitly provided, use it. Otherwise, construct from individual fields.
        This follows the pattern of supporting both URL-based and granular configuration.

        Returns:
            str: The complete database connection URL
        """
        if self.url is not None:
            return self.url

        # Construct URL from individual fields
        password_part = f":{self.password.get_secret_value()}" if self.password.get_secret_value() else ""
        return f"mysql+pymysql://{self.username}{password_part}@{self.host}:{self.port}/{self.database}"


class OpenAISettings(BaseSettings):
    api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(""), description="OpenAI API key for embeddings and chat"
    )
    model: str = Field(default="gpt-4o", description="OpenAI model for chat completions")
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI model for embeddings")
    temperature: float = Field(default=0.7, description="Temperature for chat completions")
    max_tokens: int = Field(default=1000, description="Maximum tokens for chat completions")

    model_config = SettingsConfigDict(env_prefix="OPENAI_")


class ChromaDBSettings(BaseSettings):
    """ChromaDB configuration for vector database storage and search."""

    # Book collection settings (required)
    book_persist_directory: str = Field(
        default="./chromadb_data", description="Path to ChromaDB persistence directory for book embeddings"
    )
    book_collection_name: str = Field(
        default="books_collection", description="ChromaDB collection name for book embeddings"
    )

    # FAQ collection settings (required)
    faq_persist_directory: str = Field(
        default="./chromadb_faq", description="Path to ChromaDB persistence directory for FAQ embeddings"
    )
    faq_collection_name: str = Field(
        default="faq_collection", description="ChromaDB collection name for FAQ embeddings"
    )

    model_config = SettingsConfigDict(env_prefix="CHROMADB_")

    @field_validator("book_persist_directory", "faq_persist_directory", mode="before")
    @classmethod
    def validate_persist_directory(cls, v: str) -> str:
        """Validate and normalize the persistence directory path."""
        from pathlib import Path

        return str(Path(v).resolve())


class LoggingSettings(BaseSettings):
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    model_config = SettingsConfigDict(env_prefix="LOGGING_")


class PromptSettings(BaseSettings):
    system_prompt_version: str = Field(default="v1")
    explainer_version: str = Field(default="v1")
    searcher_version: str = Field(default="v1", description="Version for searcher prompts")

    model_config = SettingsConfigDict(env_prefix="PROMPT_")

    @field_validator("system_prompt_version", "explainer_version", "searcher_version")
    @classmethod
    def validate_prompt_versions(cls, v: str, info) -> str:
        """
        Validate that the specified prompt version exists and is valid.

        Args:
            v: The version string to validate
            info: Field validation info

        Returns:
            str: The validated version string

        Raises:
            ValueError: If the version is invalid or the prompt file doesn't exist
        """
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty")

        # Validate version format (should start with 'v' followed by a number)
        if not v.startswith("v") or not v[1:].isdigit():
            raise ValueError(f"{info.field_name} must be in format 'v1', 'v2', etc. (got: {v})")

        # Check if the prompt file exists
        base_dir = BACKEND_DIR / "src" / "ai_book_seeker" / "prompts"

        if info.field_name == "system_prompt_version":
            prompt_file = base_dir / "system" / f"system_prompt_{v}.txt"
        elif info.field_name == "explainer_version":
            prompt_file = base_dir / "explainer" / f"explain_recommendation_{v}.txt"
        elif info.field_name == "searcher_version":
            prompt_file = base_dir / "searcher" / f"search_books_{v}.txt"
        else:
            # This shouldn't happen, but just in case
            return v

        if not prompt_file.exists():
            raise ValueError(f"Prompt file not found for {info.field_name}={v}. " f"Expected file: {prompt_file}")

        return v

    def get_available_versions(self) -> dict[str, list[str]]:
        """
        Get all available versions for each prompt type.

        Returns:
            dict: Mapping of prompt type to list of available versions
        """
        base_dir = BACKEND_DIR / "src" / "ai_book_seeker" / "prompts"

        available_versions = {}

        # Check system prompts
        system_dir = base_dir / "system"
        if system_dir.exists():
            system_files = [f.stem.replace("system_prompt_", "") for f in system_dir.glob("system_prompt_*.txt")]
            available_versions["system"] = sorted(system_files)

        # Check explainer prompts
        explainer_dir = base_dir / "explainer"
        if explainer_dir.exists():
            explainer_files = [
                f.stem.replace("explain_recommendation_", "")
                for f in explainer_dir.glob("explain_recommendation_*.txt")
            ]
            available_versions["explainer"] = sorted(explainer_files)

        # Check searcher prompts
        searcher_dir = base_dir / "searcher"
        if searcher_dir.exists():
            searcher_files = [f.stem.replace("search_books_", "") for f in searcher_dir.glob("search_books_*.txt")]
            available_versions["searcher"] = sorted(searcher_files)

        return available_versions

    def validate_all_versions(self) -> dict[str, bool]:
        """
        Validate that all configured versions exist.

        Returns:
            dict: Mapping of prompt type to validation status (True if valid, False if invalid)
        """
        validation_results = {}

        try:
            # This will raise ValueError if any version is invalid
            self.model_validate(self.model_dump())
            validation_results["system"] = True
            validation_results["explainer"] = True
            validation_results["searcher"] = True
        except ValueError as e:
            # Parse the error to determine which field failed
            error_msg = str(e)
            if "system_prompt_version" in error_msg:
                validation_results["system"] = False

            if "explainer_version" in error_msg:
                validation_results["explainer"] = False

            if "searcher_version" in error_msg:
                validation_results["searcher"] = False

        return validation_results


class ElevenLabsSettings(BaseSettings):
    api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(""), description="ElevenLabs API key for voice synthesis"
    )
    voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM")

    model_config = SettingsConfigDict(env_prefix="ELEVENLABS_")


class LangChainSettings(BaseSettings):
    """LangChain/LangSmith tracing and debugging configuration."""

    tracing_v2: bool = Field(default=False, description="Enable LangChain advanced tracing")
    api_key: Optional[SecretStr] = Field(default=None, description="LangSmith API key for cloud tracing")
    project: str = Field(default="ai-book-seeker", description="Project name for LangSmith tracing")

    model_config = SettingsConfigDict(env_prefix="LANGCHAIN_")


class SecuritySettings(BaseSettings):
    """Security-related configuration for API endpoints and webhooks."""

    x_api_key: Optional[SecretStr] = Field(
        default=None, description="Backend webhook secret for secure server-to-server calls"
    )

    model_config = SettingsConfigDict(env_prefix="")


class ScriptsSettings(BaseSettings):
    batch_size: int = Field(default=5)
    force_recreate: bool = Field(default=False, description="Force recreation of embeddings or other cached data")

    model_config = SettingsConfigDict(env_prefix="SCRIPTS_")


class MetadataExtractionSettings(BaseSettings):
    output_dir: str = Field(default=str(BACKEND_DIR / "metadata_extraction" / "outputs"))

    model_config = SettingsConfigDict(env_prefix="METADATA_EXTRACTION_")


class StartupSettings(BaseSettings):
    """Startup and initialization configuration for the application."""

    skip_vector_init: bool = Field(
        default=False,
        description="Skip vector database initialization during startup (useful for testing or when embeddings are pre-loaded)",
    )

    model_config = SettingsConfigDict(env_prefix="STARTUP_")


class HealthCheckSettings(BaseSettings):
    """Health check configuration for monitoring and load balancers."""

    # Timeout settings (in seconds)
    database_timeout: float = Field(default=5.0, description="Database health check timeout")
    redis_timeout: float = Field(default=3.0, description="Redis health check timeout")
    service_timeout: float = Field(default=2.0, description="Service health check timeout")

    # Caching settings
    cache_duration: int = Field(default=30, description="Health check cache duration in seconds")
    enable_caching: bool = Field(default=True, description="Enable health check result caching")

    # Feature flags for selective health checking
    enable_database_check: bool = Field(default=True, description="Enable database health checks")
    enable_redis_check: bool = Field(default=True, description="Enable Redis health checks")
    enable_chromadb_check: bool = Field(default=True, description="Enable ChromaDB health checks")
    enable_faq_check: bool = Field(default=True, description="Enable FAQ service health checks")

    # Performance monitoring
    performance_threshold_ms: int = Field(default=500, description="Performance warning threshold in milliseconds")
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")

    # API version
    version: str = Field(default="0.1.0", description="API version for health check responses")

    model_config = SettingsConfigDict(env_prefix="HEALTH_")


class AppSettings(BaseSettings):
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Application environment")
    redis: RedisSettings = Field(default_factory=RedisSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    chromadb: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    batch_size: int = Field(default=5)
    knowledge_base_path: str = Field(
        default=str(BACKEND_DIR / "src/ai_book_seeker/prompts/voice_assistant/elevenlabs/knowledge_base"),
        description="Path to the FAQ knowledge base directory",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",  # Frontend development
            "http://localhost:3001",  # Alternative frontend port
            "https://your-frontend-domain.com",  # Production frontend
        ],
        description="List of allowed CORS origins. Use ['*'] for development to allow all origins.",
    )
    interface_tool_map: Dict[str, list[str]] = Field(
        default_factory=lambda: {
            "chat": ["search_faq", "get_book_recommendation"],
            "voice": ["get_book_recommendation"],
        }
    )
    prompt_settings: PromptSettings = Field(default_factory=PromptSettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    langchain: LangChainSettings = Field(default_factory=LangChainSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    startup: StartupSettings = Field(default_factory=StartupSettings)
    health_check: HealthCheckSettings = Field(default_factory=HealthCheckSettings)
    scripts: ScriptsSettings = Field(default_factory=ScriptsSettings)
    metadata_extraction: MetadataExtractionSettings = Field(default_factory=MetadataExtractionSettings)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__", extra="ignore"
    )

    @field_validator("logging", "openai")
    @classmethod
    def validate_environment_specific_settings(cls, v, info):
        """Apply environment-specific settings based on the current environment."""
        if info.data is None:
            return v

        environment = info.data.get("environment", Environment.DEVELOPMENT)

        if info.field_name == "logging":
            # Adjust logging level based on environment
            if environment == Environment.DEVELOPMENT:
                v.level = "DEBUG"
            elif environment == Environment.TESTING:
                v.level = "INFO"
            elif environment == Environment.STAGING:
                v.level = "WARNING"
            elif environment == Environment.PRODUCTION:
                v.level = "ERROR"

        elif info.field_name == "openai":
            # Use cost-optimized model in production
            if environment == Environment.PRODUCTION:
                v.model = "gpt-4o-mini"

        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING


def create_settings() -> AppSettings:
    """
    Create a new AppSettings instance.

    This function creates a fresh AppSettings instance each time it's called.
    For FastAPI applications, settings should be stored in app.state.config
    and accessed via dependency injection.

    Returns:
        AppSettings: A new settings instance

    Example:
        >>> settings = create_settings()
        >>> print(settings.openai.model)
        >>> print(settings.redis.host)
    """
    return AppSettings()


__all__ = [
    "AppSettings",
    "create_settings",
    "Environment",
    "RedisSettings",
    "DatabaseSettings",
    "OpenAISettings",
    "ChromaDBSettings",
    "LoggingSettings",
    "PromptSettings",
    "ElevenLabsSettings",
    "LangChainSettings",
    "SecuritySettings",
    "ScriptsSettings",
    "MetadataExtractionSettings",
    "StartupSettings",
]
