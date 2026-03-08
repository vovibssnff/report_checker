from __future__ import annotations

from fastapi import APIRouter

from app.adapters.driving.web.schemas.stats import StatsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    return StatsResponse(
        total_documents=0,
        passed_count=0,
        failed_count=0,
        warning_count=0,
        pass_rate=0.0,
        common_errors=[],
    )
