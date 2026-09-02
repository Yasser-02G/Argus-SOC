import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# FortiGate logs are key=value pairs, values optionally quoted:
# date=2026-08-05 time=08:12:04 devname="FGT600E" devid="FG600E1234567890"
# logid="0000000013" type="utm" subtype="virus" level="warning"
# srcip=41.226.13.90 dstip=192.168.1.42 action="blocked" msg="File was infected/blocked"
KV_RE = re.compile(r'(\w+)=("([^"]*)"|\S+)')

LEVEL_TO_SEVERITY = {
    "emergency": "critical", "alert": "critical", "critical": "critical",
    "error": "critical", "warning": "warning", "notice": "warning",
    "information": "info", "debug": "info",
}


class FortiGateParser(BaseParser):
    source_type = "fortigate"

    def matches(self, raw: str, source_ip: str) -> bool:
        return "devid=" in raw and "logid=" in raw

    def _kv(self, raw: str) -> dict:
        out = {}
        for key, _, quoted in KV_RE.findall(raw):
            out[key] = quoted if quoted else _.strip('"')
        return out

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        fields = self._kv(raw)
        if not fields:
            return None

        try:
            ts = datetime.strptime(f"{fields.get('date')} {fields.get('time')}", "%Y-%m-%d %H:%M:%S")
            ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        level = fields.get("level", "information")
        severity = LEVEL_TO_SEVERITY.get(level, "info")

        # An explicit deny/block action on utm/ips events is always at least a warning
        if fields.get("action") in ("blocked", "deny", "dropped") and severity == "info":
            severity = "warning"

        event_type = ".".join(filter(None, [fields.get("type"), fields.get("subtype")])) or "unknown"

        return NormalizedLog(
            timestamp=ts,
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=fields.get("devname"),
            severity=severity,
            event_type=event_type,
            src_ip=fields.get("srcip"),
            dst_ip=fields.get("dstip"),
            user=fields.get("user"),
            message=fields.get("msg"),
            raw=raw,
            extra=fields,
        )


register(FortiGateParser())
