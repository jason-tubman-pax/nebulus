#!/usr/bin/env python3
"""
Seed the dashboard history DB with fake data for local development.
Run from repo root:  python scripts/seed_fake_data.py
                     .venv/bin/python scripts/seed_fake_data.py
Or:  ./scripts/seed_fake_data.sh
Optional: SEED_HOURS=48 SEED_INTERVAL_MIN=2 ./scripts/seed_fake_data.sh
"""
import asyncio
import math
import os
from datetime import datetime, timedelta, timezone

# Run from repo root so app is importable
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Sample
from app.db.session import async_session_factory, init_db


def _fake_sample(ts: datetime) -> dict:
    """Generate one fake sample for the given UTC timestamp."""
    hour = ts.hour + ts.minute / 60.0
    # Simple "sun" curve: night 0–6 and 18–24, peak at 12
    sun = max(0, math.sin((hour - 6) * math.pi / 12)) if 6 <= hour <= 18 else 0.0
    pv_power_w = 3000.0 * sun * (0.9 + 0.1 * (hash(ts.isoformat()) % 100) / 100)
    pv_voltage_v = 380.0 + 40 * sun
    pv_current_a = pv_power_w / pv_voltage_v if pv_voltage_v else 0

    # Load: base + daytime bump (W)
    load_power_w = 400.0 + 600.0 * sun + (hash(ts.isoformat()) % 200)
    load_power_w = max(100, min(2500, load_power_w))

    # Battery: charge when PV > load, discharge otherwise
    net = pv_power_w - load_power_w
    battery_power_w = net * 0.95 if net > 0 else net * 1.0  # slight charge efficiency
    battery_voltage_v = 51.2
    battery_current_a = battery_power_w / battery_voltage_v if battery_voltage_v else 0
    # SoC will be set by caller over a time series

    # Grid: fill the gap
    grid_power_w = load_power_w - pv_power_w - (-battery_power_w if battery_power_w < 0 else 0)
    if abs(grid_power_w) < 50:
        grid_power_w = 0

    return {
        "timestamp_utc": ts.replace(tzinfo=None),
        "pv_power_w": round(pv_power_w, 1),
        "pv_voltage_v": round(pv_voltage_v, 1),
        "pv_current_a": round(pv_current_a, 2),
        "battery_power_w": round(battery_power_w, 1),
        "battery_voltage_v": battery_voltage_v,
        "battery_current_a": round(battery_current_a, 2),
        "battery_temperature_c": 28.0 + (hash(ts.isoformat()) % 50) / 10,
        "grid_power_w": round(grid_power_w, 1),
        "grid_voltage_v": 230.0 + (hash(ts.isoformat()) % 20) / 10,
        "grid_frequency_hz": 50.0,
        "load_power_w": round(load_power_w, 1),
        "inverter_temperature_c": 35.0 + sun * 15,
        "status_message": "Fake data",
        "mode": "hybrid",
    }


async def seed(hours: int = 24, interval_minutes: int = 5) -> int:
    """Insert fake samples for the last `hours` at `interval_minutes` spacing. Returns count inserted."""
    await init_db()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now - timedelta(hours=hours)
    count = 0
    # SoC simulation: start at 60%, vary with battery power over time
    soc = 60.0
    dt_sec = interval_minutes * 60
    capacity_wh = 5000.0  # fake 5 kWh

    async with async_session_factory() as session:
        ts = start
        while ts <= now:
            row = _fake_sample(ts)
            # Simple SoC update: delta_soc from battery power * interval
            soc_delta = (row["battery_power_w"] * (dt_sec / 3600)) / (capacity_wh / 100) * 100
            soc = max(5, min(100, soc + soc_delta))
            row["battery_soc_percent"] = round(soc, 1)
            session.add(Sample(**row))
            count += 1
            if count % 200 == 0:
                await session.commit()
            ts += timedelta(minutes=interval_minutes)
        await session.commit()
    return count


def main() -> None:
    hours = int(os.environ.get("SEED_HOURS", "24"))
    interval = int(os.environ.get("SEED_INTERVAL_MIN", "5"))
    n = asyncio.run(seed(hours=hours, interval_minutes=interval))
    print(f"Seeded {n} fake samples (last {hours}h, interval {interval} min). Open the dashboard to see history.")


if __name__ == "__main__":
    main()
