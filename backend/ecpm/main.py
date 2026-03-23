"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Optional

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from ecpm.api.router import api_router
from ecpm.config import get_settings
from ecpm.core.logging import setup_logging
from ecpm.database import engine

logger = structlog.get_logger(__name__)

# Global Redis connection pool, initialized on startup
_redis_pool: Optional[object] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup logging, verify DB, initialize Redis."""
    global _redis_pool

    setup_logging()
    logger.info("ecpm.startup", version="0.1.0")

    # Test database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("ecpm.db_connected")
    except Exception:
        logger.warning("ecpm.db_unavailable", exc_info=True)

    # Initialize Redis connection pool
    settings = get_settings()
    try:
        import redis.asyncio as aioredis

        _redis_pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10,
        )
        # Verify connection
        await _redis_pool.ping()
        logger.info("ecpm.redis_connected", url=settings.redis_url)
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


app = FastAPI(
    title="ECPM",
    version="0.1.0",
    description="Economic Crisis Prediction Model API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
