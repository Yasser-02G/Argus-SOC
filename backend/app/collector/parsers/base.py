from abc import ABC, abstractmethod
from typing import Optional
from app.schemas import NormalizedLog


class BaseParser(ABC):
    """Every vendor parser implements this interface.

    `matches` should be cheap (a regex / substring check) since it runs
    against every incoming line to figure out which parser owns it.
    `parse` does the actual field extraction and returns a NormalizedLog.
    """

    source_type: str

    @abstractmethod
    def matches(self, raw: str, source_ip: str) -> bool: ...

    @abstractmethod
    def parse(self, raw: str, source_ip: str) -> Optional[NormalizedLog]: ...


_REGISTRY: list[BaseParser] = []


def register(parser: BaseParser) -> None:
    _REGISTRY.append(parser)


def get_parsers() -> list[BaseParser]:
    return _REGISTRY
