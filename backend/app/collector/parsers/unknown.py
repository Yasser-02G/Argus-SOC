from datetime import datetime, timezone
from typing import Optional

from app.collector.parsers.base import BaseParser
from app.schemas import NormalizedLog


class UnknownParser(BaseParser):
    """Always matches — used as a last-resort fallback so no log is ever
    dropped, even if we don't yet have a dedicated parser for its source.
    Not registered in the normal chain; the pipeline calls it explicitly
    if nothing else matched.
    """

    source_type = "unknown"

    def matches(self, raw: str, source_ip: str) -> bool:
        return True

    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]:
        return NormalizedLog(
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            source_type="unknown",
            severity="info",
            message=raw[:300],
            raw=raw,
            extra={},
        )
