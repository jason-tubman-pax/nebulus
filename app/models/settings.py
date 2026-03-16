"""Configuration and settings models."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class PersistenceConfig(BaseModel):
    """Dashboard history storage limits and rollover."""

    enabled: bool = True
    # Max size for history DB (MB). UI should cap this at available disk.
    max_storage_mb: float = 100.0
    # How often to save a sample (seconds). Higher = less data, less I/O.
    sample_interval_seconds: int = 60
    # When limit reached: delete oldest records. Optionally cap by age.
    rollover_strategy: Literal["delete_oldest", "keep_days"] = "delete_oldest"
    # If rollover_strategy == "keep_days", delete data older than this many days.
    keep_days: Optional[int] = 30


class InverterConnectionConfig(BaseModel):
    """How we connect to the inverter (Modbus)."""

    driver: str = "deye"  # deye | sofar | growatt | luxpower | victron | pylontech | ...
    connection_type: str = "tcp"  # tcp | rtu
    # TCP
    host: Optional[str] = None
    port: int = 502
    # RTU (serial)
    serial_port: Optional[str] = None  # e.g. /dev/ttyUSB0
    baudrate: int = 9600
    # Common
    slave_id: int = 1
    timeout_seconds: float = 3.0


class InverterSettings(BaseModel):
    """Writable inverter setpoints (subset; driver-dependent)."""

    # Common
    charge_power_limit_percent: Optional[int] = None  # 0–100
    discharge_power_limit_percent: Optional[int] = None
    grid_charge_enabled: Optional[bool] = None
    battery_soc_min_percent: Optional[int] = None  # stop discharge above this
    battery_soc_max_percent: Optional[int] = None  # stop charge above this
    work_mode: Optional[str] = None  # e.g. "general", "eco", "peak_shaving"
    # Extensible: driver can add more
    extra: Optional[dict[str, Any]] = None


class WifiNetwork(BaseModel):
    """Scan result or saved network."""

    ssid: str
    signal_strength: int = 0  # dBm or 0–100
    secured: bool = True
    connected: bool = False


class WifiConfig(BaseModel):
    """WiFi configuration to apply."""

    ssid: str
    password: Optional[str] = None
    # Optional: static IP
    static_ip: Optional[str] = None
    gateway: Optional[str] = None
    dns: Optional[str] = None


class TunnelState(BaseModel):
    """State of the public share tunnel."""

    enabled: bool = False
    share_url: Optional[str] = None
    tunnel_type: str = "cloudflare"
    error: Optional[str] = None


class SystemConfig(BaseModel):
    """Persisted system configuration."""

    inverter: InverterConnectionConfig = Field(default_factory=InverterConnectionConfig)
    inverter_settings: InverterSettings = Field(default_factory=InverterSettings)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    share_token: Optional[str] = None
    hostname: Optional[str] = None
