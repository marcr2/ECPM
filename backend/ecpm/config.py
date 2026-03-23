"""Application configuration via Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://ecpm:ecpm@localhost:5432/ecpm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API Keys
    fred_api_key: str = ""
    bea_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Scheduling
    fetch_schedule_hour: int = 6
    fetch_schedule_minute: int = 0

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
