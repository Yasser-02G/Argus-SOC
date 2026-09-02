import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Index, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LogEntry(Base):
    """Common normalized schema for every log source (FortiGate, ESET,
    Synology, Windows, network gear). Vendor-specific fields that don't
    map to a common column are kept in `extra` as JSONB so nothing is lost.
    """

    __tablename__ = "log_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_ip: Mapped[str] = mapped_column(String(45))          # IP that sent the syslog packet
    source_type: Mapped[str] = mapped_column(String(32), index=True)  # fortigate | eset | synology | windows | network | unknown
    source_device: Mapped[str] = mapped_column(String(128), nullable=True)  # hostname reported in the log, if any

    severity: Mapped[str] = mapped_column(String(16), index=True)  # critical | warning | info

    event_type: Mapped[str] = mapped_column(String(64), nullable=True, index=True)  # e.g. auth_fail, malware, traffic, link
    src_ip: Mapped[str] = mapped_column(String(45), nullable=True, index=True)
    dst_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    user: Mapped[str] = mapped_column(String(128), nullable=True)

    message: Mapped[str] = mapped_column(String, nullable=True)
    raw: Mapped[str] = mapped_column(String)

    extra: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_log_entries_ts_source", "timestamp", "source_type"),
    )


class Device(Base):
    """Inventory of equipment discovered from incoming syslog traffic."""

    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ip: Mapped[str] = mapped_column(String(45), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32))

    # Not derivable from syslog traffic alone — filled in manually by an
    # admin via PATCH /api/devices/{id}, or later by an SNMP/API enrichment job.
    vendor: Mapped[str] = mapped_column(String(64), nullable=True)
    model: Mapped[str] = mapped_column(String(64), nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=True)

    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    logs_count: Mapped[int] = mapped_column(default=0)


class Report(Base):
    """Metadata for a generated PDF report. The file itself lives on disk
    under REPORTS_DIR; this row is what the API/UI list and query."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(200))
    period: Mapped[str] = mapped_column(String(16))  # daily | weekly
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    filename: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(default=0)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
