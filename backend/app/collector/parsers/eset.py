import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# ESET PROTECT forwards detections/events in CEF:
# CEF:0|ESET|ESET PROTECT|1.0|4001|Malware detected|8|
#   src=192.168.1.42 duser=s.benali cs1=Trojan.GenericKD.68541812
#   act=quarantined cn1=8 dvchost=PC-COMPTA-04
CEF_HEADER_RE = re.compile(
    r"CEF:\d+\|(?P<vendor>[^|]*)\|(?P<product>[^|]*)\|(?P<version>[^|]*)\|"
    r"(?P<sig>[^|]*)\|(?P<name>[^|]*)\|(?P<sev>[^|]*)\|(?P<ext>.*)"
)
EXT_KV_RE = re.compile(r"(\w+)=((?:[^ \\]|\\ )*)")


def _cef_severity(raw_sev: str) -> str:
    try:
        n = int(raw_sev)
    except ValueError:
        return "warning"
    if n >= 7:
        return "critical"
    if n >= 4:
        return "warning"
    return "info"


class EsetParser(BaseParser):
    source_type = "eset"

    def matches(self, raw: str, source_ip: str) -> bool:
        return raw.strip().startswith("CEF:") or "ESET PROTECT" in raw

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        m = CEF_HEADER_RE.search(raw)
        if not m:
            return None

        ext = dict(EXT_KV_RE.findall(m.group("ext")))
        severity = _cef_severity(m.group("sev"))

        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=ext.get("dvchost"),
            severity=severity,
            event_type=m.group("name").strip() or "detection",
            src_ip=ext.get("src"),
            dst_ip=ext.get("dst"),
            user=ext.get("duser"),
            message=ext.get("cs1") or m.group("name").strip(),
            raw=raw,
            extra={"cef": ext, "signature_id": m.group("sig").strip(), "action": ext.get("act")},
        )


register(EsetParser())
