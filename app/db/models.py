"""SQLAlchemy models for dashboard history."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Sample(Base):
    """One stored snapshot of live data for history/charts."""

    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    pv_power_w: Mapped[float] = mapped_column(Float, default=0.0)
    pv_voltage_v: Mapped[float] = mapped_column(Float, default=0.0)
    pv_current_a: Mapped[float] = mapped_column(Float, default=0.0)

    battery_soc_percent: Mapped[float] = mapped_column(Float, default=0.0)
    battery_power_w: Mapped[float] = mapped_column(Float, default=0.0)
    battery_voltage_v: Mapped[float] = mapped_column(Float, default=0.0)
    battery_current_a: Mapped[float] = mapped_column(Float, default=0.0)
    battery_temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    grid_power_w: Mapped[float] = mapped_column(Float, default=0.0)
    grid_voltage_v: Mapped[float] = mapped_column(Float, default=0.0)
    grid_frequency_hz: Mapped[float] = mapped_column(Float, default=0.0)

    load_power_w: Mapped[float] = mapped_column(Float, default=0.0)

    inverter_temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status_message: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(64), default="")
