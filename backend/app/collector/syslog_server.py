import asyncio
import logging

from app.collector.pipeline import normalize
from app.config import settings
from app.database import async_session
from app.storage.repository import insert_log

logger = logging.getLogger("argus.syslog")


async def _handle_line(raw: str, source_ip: str) -> None:
    if not raw.strip():
        return
    try:
        normalized = normalize(raw, source_ip)
        async with async_session() as session:
            await insert_log(session, normalized)
        logger.debug("stored log source_type=%s source_ip=%s", normalized.source_type, source_ip)
    except Exception:
        logger.exception("failed to process log line from %s", source_ip)


class SyslogUDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, addr) -> None:
        source_ip = addr[0]
        text = data.decode("utf-8", errors="replace")
        asyncio.create_task(_handle_line(text, source_ip))


async def _handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    source_ip = peer[0] if peer else "unknown"
    try:
        while True:
            line = await reader.readline()
            if not line:
                break
            await _handle_line(line.decode("utf-8", errors="replace"), source_ip)
    finally:
        writer.close()


async def start_syslog_servers() -> tuple:
    """Starts UDP and TCP syslog listeners concurrently.
    Returns the transport/server handles so the caller can close them
    gracefully on shutdown.
    """
    loop = asyncio.get_running_loop()

    udp_transport, _ = await loop.create_datagram_endpoint(
        SyslogUDPProtocol, local_addr=(settings.syslog_host, settings.syslog_udp_port)
    )
    logger.info("syslog UDP listening on %s:%s", settings.syslog_host, settings.syslog_udp_port)

    tcp_server = await asyncio.start_server(
        _handle_tcp_client, host=settings.syslog_host, port=settings.syslog_tcp_port
    )
    logger.info("syslog TCP listening on %s:%s", settings.syslog_host, settings.syslog_tcp_port)

    return udp_transport, tcp_server
