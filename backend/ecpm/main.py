"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from ecpm.core.logging import setup_logging
from ecpm.database import engine

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: setup logging and verify DB connection on startup."""
    setup_logging()
    logger.info("ecpm.startup", version="0.1.0")

    # Test database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("ecpm.db_connected")
    except Exception:
        logger.warning("ecpm.db_unavailable", exc_info=True)

    yield

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


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
