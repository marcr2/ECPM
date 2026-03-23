"""Aggregate API router combining all sub-routers.

Collects data and status routers into a single router for inclusion
in the FastAPI application.
"""

from fastapi import APIRouter

from ecpm.api.data import router as data_router
from ecpm.api.status import router as status_router

api_router = APIRouter()

api_router.include_router(data_router)
api_router.include_router(status_router)
