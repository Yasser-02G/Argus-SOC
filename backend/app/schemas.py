from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

Severity = Literal["critical", "warning", "info"]
SourceType = Literal["fortigate", "eset", "synology", "windows", "linux", "network", "unknown"]


class NormalizedLog(BaseModel):
    """The single common shape every vendor's raw log gets converted into
    before it is stored. This is the contract the AI agent (Phase 2) and
    the API will rely on, regardless of which device produced the log.
    """

    timestamp: datetime
    source_ip: str
    source_type: SourceType
    source_device: Optional[str] = None

    severity: Severity

    event_type: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    user: Optional[str] = None

    message: Optional[str] = None
    raw: str

    extra: dict = Field(default_factory=dict)


class LogOut(BaseModel):
    id: str
    timestamp: datetime
    source_ip: str
    source_type: str
    source_device: Optional[str] = None
    severity: str
    event_type: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    user: Optional[str] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


class DeviceOut(BaseModel):
    id: str
    ip: str
    name: Optional[str] = None
    source_type: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    status: str  # computed: "online" | "degraded" — based on last_seen recency
    first_seen: datetime
    last_seen: datetime
    logs_count: int

    class Config:
        from_attributes = True


class DeviceUpdate(BaseModel):
    """Manual enrichment — syslog alone doesn't tell us the vendor/model."""
    vendor: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None


class SeverityCount(BaseModel):
    severity: str
    count: int


class CategoryCount(BaseModel):
    category: str
    count: int


class HourlyPoint(BaseModel):
    hour: str  # "00".."23"
    source_type: str
    count: int


class StatsOverview(BaseModel):
    total_events_today: int
    severity_counts: list[SeverityCount]
    top_categories: list[CategoryCount]
    hourly_volume: list[HourlyPoint]


class ChatTurn(BaseModel):
    role: Literal["user", "agent"]
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = Field(default_factory=list)


class ToolCallOut(BaseModel):
    name: str
    args: dict


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallOut]


class ReportOut(BaseModel):
    id: str
    name: str
    period: str
    period_start: datetime
    period_end: datetime
    filename: str
    size_bytes: int
    generated_at: datetime

    class Config:
        from_attributes = True


class GenerateReportRequest(BaseModel):
    period: Literal["daily", "weekly"] = "daily"
