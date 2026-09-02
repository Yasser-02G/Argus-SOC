import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.reports.service import generate_report
from app.schemas import ReportOut, GenerateReportRequest
from app.storage.repository import list_reports, get_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=list[ReportOut])
async def get_reports(session: AsyncSession = Depends(get_session)):
    reports = await list_reports(session)
    return [ReportOut.model_validate({**r.__dict__, "id": str(r.id)}) for r in reports]


@router.post("/generate", response_model=ReportOut)
async def post_generate_report(payload: GenerateReportRequest, session: AsyncSession = Depends(get_session)):
    report = await generate_report(session, period=payload.period)
    return ReportOut.model_validate({**report.__dict__, "id": str(report.id)})


@router.get("/{report_id}/download")
async def download_report(report_id: str, session: AsyncSession = Depends(get_session)):
    report = await get_report(session, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    filepath = os.path.join(settings.reports_dir, report.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file missing on disk")
    return FileResponse(filepath, media_type="application/pdf", filename=report.filename)
