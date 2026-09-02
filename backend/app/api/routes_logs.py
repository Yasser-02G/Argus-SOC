from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import LogOut
from app.storage.repository import query_logs

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=list[LogOut])
async def get_logs(
    source_type: Optional[str] = Query(None, description="fortigate | eset | synology | windows | network"),
    severity: Optional[str] = Query(None, description="critical | warning | info"),
    q: Optional[str] = Query(None, description="Full-text search on message, IPs, hostname"),
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    logs = await query_logs(
        session, source_type=source_type, severity=severity, q=q,
        since=since, until=until, limit=limit, offset=offset,
    )
    return [LogOut.model_validate({**l.__dict__, "id": str(l.id)}) for l in logs]
