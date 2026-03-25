"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Optional

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from ecpm.api.router import api_router
from ecpm.config import get_settings
from ecpm.core.logging import setup_logging
from ecpm.database import engine
from ecpm.middleware.exception_handler import register_exception_handlers
from ecpm.middleware.rate_limit import limiter
from ecpm.middleware.request_size_limit import RequestSizeLimitMiddleware
from ecpm.middleware.security_headers import SecurityHeadersMiddleware

logger = structlog.get_logger(__name__)

# Global Redis connection pool, initialized on startup
_redis_pool: Optional[object] = None


def _cors_allow_origins() -> list[str]:
    settings = get_settings()
    raw = settings.cors_origins.strip()
    if not raw:
        return ["http://localhost:3000"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup logging, verify DB, initialize Redis."""
    global _redis_pool

    setup_logging()
    logger.info("ecpm.startup", version="0.1.0")

    settings = get_settings()
    if settings.environment == "production" and not settings.jwt_secret_key.strip():
        raise RuntimeError(
            "JWT_SECRET_KEY must be set when ENVIRONMENT=production "
            "(auth and training flows require a strong signing secret)."
        )
    if settings.environment == "production" and not settings.admin_password_hash.strip():
        logger.warning(
            "ecpm.prod_admin_hash_missing",
            msg="ADMIN_PASSWORD_HASH is empty; set it (see scripts/create_admin.py) before using admin login.",
        )

    # Test database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("ecpm.db_connected")
    except Exception:
        logger.warning("ecpm.db_unavailable", exc_info=True)

    # Initialize Redis connection pool
    try:
        import redis.asyncio as aioredis

        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10,
        )
        # Verify connection
        await _redis_pool.ping()
        logger.info("ecpm.redis_connected")
    except ImportError:
        logger.warning("ecpm.redis_unavailable", msg="redis.asyncio not installed")
        _redis_pool = None
    except Exception:
        logger.warning("ecpm.redis_unavailable", exc_info=True)
        _redis_pool = None

    yield

    # Cleanup
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None

    await engine.dispose()
    logger.info("ecpm.shutdown")


def _create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    is_prod = settings.environment == "production"

    application = FastAPI(
        title="ECPM",
        version="0.1.0",
        description="Economic Crisis Prediction Model API",
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(RequestSizeLimitMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["X-Request-ID"],
    )

    # Rate limiter: use Redis backend if available
    if settings.redis_password:
        limiter._storage_uri = settings.redis_url
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    register_exception_handlers(application)

    application.include_router(api_router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    return application


app = _create_app()
