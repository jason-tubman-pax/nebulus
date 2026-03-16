"""Real-time data models for dashboard (from Modbus)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LiveData(BaseModel):
    """Single snapshot of inverter/battery/solar state."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # PV
    pv_power_w: float = 0.0
    pv_voltage_v: float = 0.0
    pv_current_a: float = 0.0

    # Battery
    battery_soc_percent: float = 0.0
    battery_power_w: float = 0.0  # positive = charging
    battery_voltage_v: float = 0.0
    battery_current_a: float = 0.0
    battery_temperature_c: Optional[float] = None

    # Grid
    grid_power_w: float = 0.0  # positive = import
    grid_voltage_v: float = 0.0
    grid_frequency_hz: float = 0.0

    # Load / AC output
    load_power_w: float = 0.0

    # Inverter status
    inverter_temperature_c: Optional[float] = None
    status_message: str = ""
    mode: str = ""  # e.g. "grid", "battery", "hybrid"

    # Optional: battery cycles, etc.
    battery_cycles: Optional[int] = None
