import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session
from app.reports.service import generate_report

logger = logging.getLogger("argus.scheduler")


async def _run_scheduled(period: str) -> None:
    async with async_session() as session:
        try:
            await generate_report(session, period=period)
        except Exception:
            logger.exception("scheduled report generation failed (period=%s)", period)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Quotidien à 05:00 UTC
    scheduler.add_job(_run_scheduled, CronTrigger(hour=5, minute=0), args=["daily"], id="daily_report", replace_existing=True)
    # Hebdomadaire le lundi à 06:00 UTC
    scheduler.add_job(_run_scheduled, CronTrigger(day_of_week="mon", hour=6, minute=0), args=["weekly"], id="weekly_report", replace_existing=True)
    scheduler.start()
    logger.info("report scheduler started (daily 05:00 UTC, weekly Mon 06:00 UTC)")
    return scheduler
