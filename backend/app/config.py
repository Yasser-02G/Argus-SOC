from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://argus:argus@localhost:5432/argus"

    syslog_host: str = "0.0.0.0"
    syslog_udp_port: int = 5514
    syslog_tcp_port: int = 5514

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Agent IA — clé gratuite sur https://aistudio.google.com/apikey
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Rapports PDF
    reports_dir: str = "/app/data/reports"
    enable_scheduled_reports: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
