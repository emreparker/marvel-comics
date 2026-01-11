"""Configuration management using pydantic-settings.

Settings can be configured via environment variables or .env file.
All environment variables are prefixed with MARVEL_.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    All settings can be overridden via environment variables
    prefixed with MARVEL_ (e.g., MARVEL_DB_PATH, MARVEL_API_PORT).
    """

    model_config = SettingsConfigDict(
        env_prefix="MARVEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    db_path: Path = Field(
        default=Path("data/marvel.db"),
        description="Path to SQLite database file",
    )

    # API Server
    api_host: str = Field(
        default="127.0.0.1",
        description="API server host",
    )
    api_port: int = Field(
        default=8787,
        description="API server port",
    )
    api_reload: bool = Field(
        default=False,
        description="Enable auto-reload (development only)",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        default=60,
        description="Max requests per minute per IP",
    )
    rate_limit_burst: int = Field(
        default=30,
        description="Burst allowance for rate limiting",
    )

    # Caching
    cache_ttl_seconds: int = Field(
        default=86400,  # 1 day
        description="Cache-Control max-age for issue data",
    )

    # Scraping (internal use)
    scrape_delay: float = Field(
        default=0.2,
        description="Delay between scrape requests in seconds",
    )
    scrape_timeout: float = Field(
        default=60.0,
        description="HTTP request timeout in seconds",
    )
    scrape_max_retries: int = Field(
        default=3,
        description="Max retry attempts for failed requests",
    )
    scrape_max_years: Optional[int] = Field(
        default=None,
        description="Max years to scrape per run (for politeness)",
    )
    user_agent: str = Field(
        default="marvel-metadata/1.0.0 (+https://github.com/emreparker/marvel-metadata)",
        description="User-Agent header for HTTP requests",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )
    log_format: Literal["json", "text"] = Field(
        default="text",
        description="Log format (json for production, text for development)",
    )


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Settings are loaded once and cached.

    Returns:
        Settings instance

    Example:
        >>> settings = get_settings()
        >>> print(settings.db_path)
        data/marvel.db
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment.

    Useful for testing or after environment changes.

    Returns:
        Fresh Settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
