import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# Cisco-style network gear (switches, routers) syslog:
# %LINK-3-UPDOWN: Interface GigabitEthernet1/0/14, changed state to up
# %SEC-6-IPACCESSLOGP: list 101 denied tcp 203.0.113.4(0) -> 10.0.0.1(22)
FACILITY_RE = re.compile(r"%(?P<facility>[\w]+)-(?P<sev>\d)-(?P<mnemonic>[\w]+):\s*(?P<msg>.*)")

# Cisco severity 0-7 -> our 3-tier scale
CISCO_SEVERITY = {
    "0": "critical", "1": "critical", "2": "critical", "3": "critical",
    "4": "warning", "5": "warning",
    "6": "info", "7": "info",
}

IP_PAIR_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})\(\d+\)\s*->\s*(\d{1,3}(?:\.\d{1,3}){3})")
UPDOWN_STATE_RE = re.compile(r"changed state to (\w+)", re.IGNORECASE)


def _severity_for_updown(mnemonic: str, msg: str, fallback: str) -> str:
    """Cisco logs LINK-UPDOWN at severity 3 ("errors") by convention,
    regardless of whether the interface came up or went down. That means
    a link *recovering* would otherwise be reported as critical, which is
    misleading for an admin (or an AI summarizing the day). We only trust
    the raw Cisco severity for a state going down; "up" is downgraded to
    info since it's a recovery, not an incident.
    """
    if mnemonic.upper() != "UPDOWN":
        return fallback
    state_match = UPDOWN_STATE_RE.search(msg)
    if not state_match:
        return fallback
    state = state_match.group(1).lower()
    if state == "up":
        return "info"
    if state == "down":
        return "warning" if fallback == "critical" else fallback
    return fallback


class NetworkParser(BaseParser):
    source_type = "network"

    def matches(self, raw: str, source_ip: str) -> bool:
        return bool(FACILITY_RE.search(raw))

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        m = FACILITY_RE.search(raw)
        if not m:
            return None

        severity = CISCO_SEVERITY.get(m.group("sev"), "info")
        severity = _severity_for_updown(m.group("mnemonic"), m.group("msg"), severity)
        ip_pair = IP_PAIR_RE.search(m.group("msg"))

        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=None,
            severity=severity,
            event_type=f"{m.group('facility')}.{m.group('mnemonic')}".lower(),
            src_ip=ip_pair.group(1) if ip_pair else None,
            dst_ip=ip_pair.group(2) if ip_pair else None,
            message=m.group("msg"),
            raw=raw,
            extra={"facility": m.group("facility"), "mnemonic": m.group("mnemonic")},
        )


register(NetworkParser())
