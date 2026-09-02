from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LogEntry, Device, Report
from app.schemas import NormalizedLog, DeviceUpdate

# event_type (as produced by the parsers) -> display category used on the
# dashboard ("Malware", "Intrusion", "Auth", "Network", "Storage", "Autres")
CATEGORY_MAP = {
    "utm.virus": "Malware", "detection": "Malware", "malware": "Malware",
    "ips.signature": "Intrusion", "intrusion": "Intrusion",
    "auth_fail": "Auth", "auth_success": "Auth", "account_lockout": "Auth",
    "account_created": "Auth", "account_deleted": "Auth", "group_membership_change": "Auth",
    "linux.sshd": "Auth", "linux.sudo": "Auth", "linux.su": "Auth", "privilege_escalation": "Auth",
    "traffic.forward": "Network", "link.updown": "Network", "network": "Network",
    "backup": "Storage", "storage": "Storage",
}


def _categorize(event_type: Optional[str]) -> str:
    if not event_type:
        return "Autres"
    return CATEGORY_MAP.get(event_type, "Autres")


def _device_status(last_seen: datetime, threshold_minutes: int = 5) -> str:
    now = datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)
    return "online" if (now - last_seen) < timedelta(minutes=threshold_minutes) else "degraded"


async def insert_log(session: AsyncSession, log: NormalizedLog) -> LogEntry:
    entry = LogEntry(
        timestamp=log.timestamp,
        source_ip=log.source_ip,
        source_type=log.source_type,
        source_device=log.source_device,
        severity=log.severity,
        event_type=log.event_type,
        src_ip=log.src_ip,
        dst_ip=log.dst_ip,
        user=log.user,
        message=log.message,
        raw=log.raw,
        extra=log.extra,
    )
    session.add(entry)
    await _touch_device(session, log)
    await session.commit()
    return entry


async def _touch_device(session: AsyncSession, log: NormalizedLog) -> None:
    """Create or update the device inventory entry for whoever sent this log."""
    result = await session.execute(select(Device).where(Device.ip == log.source_ip))
    device = result.scalar_one_or_none()

    if device is None:
        device = Device(
            ip=log.source_ip,
            name=log.source_device,
            source_type=log.source_type,
            logs_count=1,
        )
        session.add(device)
    else:
        device.last_seen = datetime.now(timezone.utc)
        device.logs_count += 1
        if log.source_device and not device.name:
            device.name = log.source_device


async def query_logs(
    session: AsyncSession,
    source_type: Optional[str] = None,
    severity: Optional[str] = None,
    q: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
):
    stmt = select(LogEntry).order_by(LogEntry.timestamp.desc())

    if source_type:
        stmt = stmt.where(LogEntry.source_type == source_type)
    if severity:
        stmt = stmt.where(LogEntry.severity == severity)
    if since:
        stmt = stmt.where(LogEntry.timestamp >= since)
    if until:
        stmt = stmt.where(LogEntry.timestamp <= until)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            (LogEntry.message.ilike(like))
            | (LogEntry.src_ip.ilike(like))
            | (LogEntry.dst_ip.ilike(like))
            | (LogEntry.source_device.ilike(like))
        )

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_devices(session: AsyncSession):
    result = await session.execute(select(Device).order_by(Device.last_seen.desc()))
    devices = result.scalars().all()
    # attach computed status without persisting it
    for d in devices:
        d.status = _device_status(d.last_seen)
    return devices


async def update_device(session: AsyncSession, device_id, patch: DeviceUpdate) -> Optional[Device]:
    result = await session.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if device is None:
        return None
    for field, value in patch.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await session.commit()
    device.status = _device_status(device.last_seen)
    return device


async def stats_overview(session: AsyncSession, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    total_result = await session.execute(
        select(func.count(LogEntry.id)).where(LogEntry.timestamp >= since)
    )
    total_events_today = total_result.scalar_one()

    sev_result = await session.execute(
        select(LogEntry.severity, func.count(LogEntry.id))
        .where(LogEntry.timestamp >= since)
        .group_by(LogEntry.severity)
    )
    severity_counts = [{"severity": s, "count": c} for s, c in sev_result.all()]

    cat_result = await session.execute(
        select(LogEntry.event_type, func.count(LogEntry.id))
        .where(LogEntry.timestamp >= since)
        .group_by(LogEntry.event_type)
    )
    category_totals: dict[str, int] = {}
    for event_type, count in cat_result.all():
        cat = _categorize(event_type)
        category_totals[cat] = category_totals.get(cat, 0) + count
    top_categories = sorted(
        [{"category": k, "count": v} for k, v in category_totals.items()],
        key=lambda x: -x["count"],
    )

    hourly_result = await session.execute(
        select(
            func.to_char(LogEntry.timestamp, "HH24").label("hour"),
            LogEntry.source_type,
            func.count(LogEntry.id),
        )
        .where(LogEntry.timestamp >= since)
        .group_by("hour", LogEntry.source_type)
        .order_by("hour")
    )
    hourly_volume = [{"hour": h, "source_type": s, "count": c} for h, s, c in hourly_result.all()]

    return {
        "total_events_today": total_events_today,
        "severity_counts": severity_counts,
        "top_categories": top_categories,
        "hourly_volume": hourly_volume,
    }


async def insert_report(session: AsyncSession, *, name, period, period_start, period_end, filename, size_bytes) -> Report:
    report = Report(
        name=name, period=period, period_start=period_start, period_end=period_end,
        filename=filename, size_bytes=size_bytes,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def list_reports(session: AsyncSession, limit: int = 50):
    result = await session.execute(
        select(Report).order_by(Report.generated_at.desc()).limit(limit)
    )
    return result.scalars().all()


async def get_report(session: AsyncSession, report_id):
    result = await session.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()
