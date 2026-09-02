# Importing each parser module triggers its `register()` call at the
# bottom of the file, populating the shared registry in `base.py`.
from app.collector.parsers import fortigate, eset, synology, windows, network, linux  # noqa: F401
from app.collector.parsers.unknown import UnknownParser

FALLBACK = UnknownParser()
