"""Cache management API endpoints.

Provides endpoints to manually trigger cache refresh and view cache status.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ecpm.cache_manager import invalidate_cache
from ecpm.tasks.cache_tasks import precompute_all_indicators

router = APIRouter(prefix="/api/cache", tags=["cache"])


class CacheRefreshResponse(BaseModel):
    """Response for cache refresh operation."""

    status: str
    message: str
    results: dict[str, int]


class CacheInvalidateResponse(BaseModel):
    """Response for cache invalidation operation."""

    status: str
    message: str
    files_deleted: int


@router.post("/refresh", response_model=CacheRefreshResponse)
async def refresh_cache() -> CacheRefreshResponse:
    """Manually trigger a full cache refresh.

    Computes all indicators for all methodologies and stores results to disk.
    This operation may take several minutes to complete.
    """
    try:
        results = await precompute_all_indicators()
        return CacheRefreshResponse(
            status="success",
            message="Cache refresh completed successfully",
            results=results,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache refresh failed: {str(e)}",
        )


@router.post("/invalidate", response_model=CacheInvalidateResponse)
async def invalidate_all_cache(
    methodology: str | None = None,
    slug: str | None = None,
) -> CacheInvalidateResponse:
    """Invalidate (delete) cached files.

    Query parameters:
    - methodology: Optional methodology slug. If omitted, invalidates all.
    - slug: Optional indicator slug. If omitted, invalidates all for methodology.
    """
    files_deleted = invalidate_cache(methodology=methodology, slug=slug)

    return CacheInvalidateResponse(
        status="success",
        message=f"Invalidated {files_deleted} cache files",
        files_deleted=files_deleted,
    )
