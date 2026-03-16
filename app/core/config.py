"""Application configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _config_dir() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PAX_",
        extra="ignore",
    )

    app_name: str = "Pax Nebulus"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Modbus
    modbus_poll_interval_seconds: float = 2.0

    # Paths
    data_dir: Path = _config_dir()
    config_file: str = "config.json"

    # Tunnel (share link)
    tunnel_type: str = "cloudflare"  # cloudflare | localtunnel
    cloudflared_path: str = "cloudflared"
    localtunnel_path: str = "lt"

    @property
    def config_path(self) -> Path:
        return self.data_dir / self.config_file


settings = Settings()
