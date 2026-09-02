from app.collector.parsers import FALLBACK
from app.collector.parsers.base import get_parsers
from app.schemas import NormalizedLog


def normalize(raw: str, source_ip: str) -> NormalizedLog:
    """Try each registered parser in order; fall back to the generic
    parser so every received line is stored, even unrecognized ones.
    """
    raw = raw.strip()
    for parser in get_parsers():
        if parser.matches(raw, source_ip):
            result = parser.parse(raw, source_ip)
            if result is not None:
                return result
    return FALLBACK.parse(raw, source_ip)
