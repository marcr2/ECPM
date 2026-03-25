"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env.local file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (individual fields -- no embedded credentials in defaults)
    postgres_user: str = "ecpm"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ecpm"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    # API Keys
    fred_api_key: str = ""
    bea_api_key: str = ""
    census_api_key: str = ""

    # SEC EDGAR (no key needed, but fair-access policy requires User-Agent)
    edgar_user_agent: str = ""

    # JWT Authentication
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Admin bootstrap credentials (hashed at first use, then discard)
    admin_username: str = "admin"
    admin_password_hash: str = ""

    # Static token for triggering model training (API-only, no UI)
    training_token: str = ""

    # Scheduling
    fetch_schedule_hour: int = 6
    fetch_schedule_minute: int = 0

    # Logging
    log_level: str = "INFO"

    # Environment
    environment: str = "development"

    # Comma-separated browser origins for CORS (e.g. https://app.example.com).
    # Empty: default allows http://localhost:3000 only.
    cors_origins: str = ""

    # Optional extra CSP connect-src tokens (space- or comma-separated URLs), for
    # split-origin API hosts. Same-origin reverse proxy needs no extra values.
    csp_connect_src_extra: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        pw = quote_plus(self.postgres_password) if self.postgres_password else ""
        userinfo = f"{self.postgres_user}:{pw}" if pw else self.postgres_user
        return (
            f"postgresql+asyncpg://{userinfo}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker_url(self) -> str:
        if self.redis_password:
            return f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/1"
        return f"redis://{self.redis_host}:{self.redis_port}/1"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_result_backend(self) -> str:
        if self.redis_password:
            return f"redis://:{quote_plus(self.redis_password)}@{self.redis_host}:{self.redis_port}/2"
        return f"redis://{self.redis_host}:{self.redis_port}/2"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
