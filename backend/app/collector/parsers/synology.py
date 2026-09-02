import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# Synology DSM Log Center forwards free-text lines such as:
# Synology-NAS-01 SYSTEM: Info User [admin] from [192.168.1.5] logged in successfully via [DSM].
# Synology-NAS-01 SYSTEM: Warning The free space of volume 1 has fallen below 10GB.
# Synology-NAS-01 Backup: Info The Hyper Backup task "Daily-Backup" has been completed.
LINE_RE = re.compile(
    r"^(?P<host>[\w-]+)\s+(?P<category>[\w]+):\s*(?P<level>Info|Warning|Error|Notice)\s+(?P<msg>.*)$"
)

LEVEL_TO_SEVERITY = {"Error": "critical", "Warning": "warning", "Notice": "warning", "Info": "info"}

CATEGORY_EVENT = {
    "SYSTEM": "system", "Backup": "backup", "Security": "security",
    "Connection": "network", "SecurityScan": "security",
}

IP_RE = re.compile(r"\[(\d{1,3}(?:\.\d{1,3}){3})\]")
USER_RE = re.compile(r"User \[([^\]]+)\]")


class SynologyParser(BaseParser):
    source_type = "synology"

    def matches(self, raw: str, source_ip: str) -> bool:
        return bool(LINE_RE.match(raw.strip())) and "synology" in raw.lower() or "Hyper Backup" in raw

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        m = LINE_RE.match(raw.strip())
        if not m:
            return None

        severity = LEVEL_TO_SEVERITY.get(m.group("level"), "info")
        msg = m.group("msg")
        ip_match = IP_RE.search(msg)
        user_match = USER_RE.search(msg)

        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=m.group("host"),
            severity=severity,
            event_type=CATEGORY_EVENT.get(m.group("category"), m.group("category").lower()),
            src_ip=ip_match.group(1) if ip_match else None,
            user=user_match.group(1) if user_match else None,
            message=msg,
            raw=raw,
            extra={"category": m.group("category")},
        )


register(SynologyParser())
