import re
from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser, register
from app.schemas import NormalizedLog

# Syslog natif Ubuntu/Linux (rsyslog forward de /var/log/auth.log notamment) :
# ubuntu-edr-01 sshd[1234]: Failed password for admin from 203.0.113.4 port 51422 ssh2
# ubuntu-edr-01 sshd[1234]: Accepted password for admin from 192.168.1.50 port 22 ssh2
# ubuntu-edr-01 sudo: sbenali : TTY=pts/0 ; PWD=/home/sbenali ; USER=root ; COMMAND=/usr/bin/apt update
HOST_RE = re.compile(r"^([\w.-]+)\s+(sshd|sudo|su)(\[\d+\])?:\s*(.*)$")
SSH_FAIL_RE = re.compile(r"Failed password for (invalid user )?(\S+) from (\d{1,3}(?:\.\d{1,3}){3})")
SSH_OK_RE = re.compile(r"Accepted (password|publickey) for (\S+) from (\d{1,3}(?:\.\d{1,3}){3})")
SUDO_RE = re.compile(r"^(\S+)\s*:.*COMMAND=(.*)$")


class LinuxParser(BaseParser):
    source_type = "linux"

    def matches(self, raw: str, source_ip: str) -> bool:
        return bool(HOST_RE.match(raw.strip()))

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        m = HOST_RE.match(raw.strip())
        if not m:
            return None
        host, program, _, msg = m.groups()

        severity, event_type, user, src_ip = "info", f"linux.{program}", None, None

        if program == "sshd":
            fail = SSH_FAIL_RE.search(msg)
            ok = SSH_OK_RE.search(msg)
            if fail:
                severity, event_type = "warning", "auth_fail"
                user, src_ip = fail.group(2), fail.group(3)
            elif ok:
                severity, event_type = "info", "auth_success"
                user, src_ip = ok.group(2), ok.group(3)
        elif program in ("sudo", "su"):
            sudo_m = SUDO_RE.match(msg)
            severity, event_type = "warning", "privilege_escalation"
            if sudo_m:
                user = sudo_m.group(1)

        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type=self.source_type,
            source_device=host,
            severity=severity,
            event_type=event_type,
            src_ip=src_ip,
            user=user,
            message=msg,
            raw=raw,
            extra={"program": program},
        )


register(LinuxParser())
