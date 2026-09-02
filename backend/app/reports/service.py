import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.reports.generator import build_report_pdf
from app.storage.repository import query_logs, stats_overview, list_devices, insert_report

logger = logging.getLogger("argus.reports")

PERIOD_HOURS = {"daily": 24, "weekly": 24 * 7}
PERIOD_LABEL = {"daily": "Rapport quotidien", "weekly": "Rapport hebdomadaire"}


def _serialize_log(entry) -> dict:
    return {
        "timestamp": entry.timestamp, "source_type": entry.source_type,
        "severity": entry.severity, "event_type": entry.event_type,
        "message": entry.message,
    }


def _serialize_device(d) -> dict:
    return {"name": d.name, "ip": d.ip, "status": getattr(d, "status", None), "logs_count": d.logs_count}


async def generate_report(session: AsyncSession, period: str = "daily") -> dict:
    hours = PERIOD_HOURS.get(period, 24)
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(hours=hours)

    stats = await stats_overview(session, hours=hours)
    critical_logs = await query_logs(session, severity="critical", since=period_start, limit=50)
    devices = await list_devices(session)

    pdf_bytes = build_report_pdf(
        period_label=PERIOD_LABEL.get(period, "Rapport"),
        period_start=period_start,
        period_end=period_end,
        stats=stats,
        critical_logs=[_serialize_log(l) for l in critical_logs],
        devices=[_serialize_device(d) for d in devices],
    )

    os.makedirs(settings.reports_dir, exist_ok=True)
    stamp = period_end.strftime("%Y%m%d-%H%M%S")
    filename = f"argus-{period}-{stamp}.pdf"
    filepath = os.path.join(settings.reports_dir, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

    name = f"{PERIOD_LABEL.get(period, 'Rapport')} - {period_end.strftime('%d/%m/%Y %H:%M')}"
    report = await insert_report(
        session, name=name, period=period, period_start=period_start, period_end=period_end,
        filename=filename, size_bytes=len(pdf_bytes),
    )
    logger.info("report generated: %s (%d bytes)", filename, len(pdf_bytes))
    return report
