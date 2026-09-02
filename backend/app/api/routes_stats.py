from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import StatsOverview
from app.storage.repository import stats_overview

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
async def get_overview(
    hours: int = Query(24, le=168, description="Fenêtre glissante en heures"),
    session: AsyncSession = Depends(get_session),
):
    return await stats_overview(session, hours=hours)
