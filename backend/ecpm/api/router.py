"""Aggregate API router combining all sub-routers.

Collects data, status, and indicator routers into a single router for
inclusion in the FastAPI application.

Note: Methodology documentation routes are defined within the indicators
router (before dynamic {slug} routes) to avoid route ordering conflicts.
"""

from fastapi import APIRouter

from ecpm.api.data import router as data_router
from ecpm.api.indicators import router as indicators_router
from ecpm.api.status import router as status_router

api_router = APIRouter()

api_router.include_router(data_router)
api_router.include_router(status_router)
api_router.include_router(indicators_router)
