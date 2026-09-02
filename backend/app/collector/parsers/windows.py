import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# Windows Event Logs reach syslog via a forwarding agent (NXLog, Snare, etc.)
# Typical flattened line:
# WIN-DC01 MSWinEventLog Security 4625 Microsoft-Windows-Security-Auditing
#   Account Name: j.dupont Source Network Address: 192.168.1.77 ...
EVENTID_RE = re.compile(r"EventID[:=]?\s*(\d+)")
ACCOUNT_RE = re.compile(r"Account Name:\s*([^\s,]+)")
SRC_IP_RE = re.compile(r"Source Network Address:\s*(\d{1,3}(?:\.\d{1,3}){3})")
HOST_RE = re.compile(r"^([\w-]+)\s+MSWinEventLog")

# EventID -> (severity, event_type)
EVENT_MAP = {
    "4624": ("info", "auth_success"),
    "4625": ("warning", "auth_fail"),
    "4720": ("warning", "account_created"),
    "4726": ("warning", "account_deleted"),
    "4732": ("warning", "group_membership_change"),
    "4740": ("warning", "account_lockout"),
    "1102": ("critical", "audit_log_cleared"),
    "4688": ("info", "process_created"),
}


class WindowsParser(BaseParser):
    source_type = "windows"

    def matches(self, raw: str, source_ip: str) -> bool:
        return "MSWinEventLog" in raw or bool(EVENTID_RE.search(raw))

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        event_id_m = EVENTID_RE.search(raw)
        if not event_id_m:
            return None
        event_id = event_id_m.group(1)

        severity, event_type = EVENT_MAP.get(event_id, ("info", f"event_{event_id}"))

        host_m = HOST_RE.search(raw)
        account_m = ACCOUNT_RE.search(raw)
        srcip_m = SRC_IP_RE.search(raw)

        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=host_m.group(1) if host_m else None,
            severity=severity,
            event_type=event_type,
            src_ip=srcip_m.group(1) if srcip_m else None,
            user=account_m.group(1) if account_m else None,
            message=raw.split("MSWinEventLog", 1)[-1].strip()[:300],
            raw=raw,
            extra={"event_id": event_id},
        )


register(WindowsParser())
