import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_logs, routes_devices, routes_stats, routes_agent, routes_reports
from app.collector.syslog_server import start_syslog_servers
from app.config import settings
from app.database import init_models
from app.reports.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    udp_transport, tcp_server = await start_syslog_servers()
    scheduler = start_scheduler() if settings.enable_scheduled_reports else None
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    udp_transport.close()
    tcp_server.close()
    await tcp_server.wait_closed()


app = FastAPI(title="ARGUS SOC — Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_logs.router)
app.include_router(routes_devices.router)
app.include_router(routes_stats.router)
app.include_router(routes_agent.router)
app.include_router(routes_reports.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
