"""Dashboard history persistence with configurable storage limits and rollover."""
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Sample
from app.db.session import async_session_factory
from app.models.live import LiveData
from app.services.config_store import config_store

# Approximate bytes per row for size estimation (SQLite row overhead + columns)
BYTES_PER_ROW = 250


def _live_to_row(data: LiveData) -> dict:
    ts = data.timestamp
    if ts.tzinfo:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
    return {
        "timestamp_utc": ts,
        "pv_power_w": data.pv_power_w,
        "pv_voltage_v": data.pv_voltage_v,
        "pv_current_a": data.pv_current_a,
        "battery_soc_percent": data.battery_soc_percent,
        "battery_power_w": data.battery_power_w,
        "battery_voltage_v": data.battery_voltage_v,
        "battery_current_a": data.battery_current_a,
        "battery_temperature_c": data.battery_temperature_c,
        "grid_power_w": data.grid_power_w,
        "grid_voltage_v": data.grid_voltage_v,
        "grid_frequency_hz": data.grid_frequency_hz,
        "load_power_w": data.load_power_w,
        "inverter_temperature_c": data.inverter_temperature_c,
        "status_message": data.status_message or "",
        "mode": data.mode or "",
    }


async def save_sample(data: LiveData) -> None:
    """Append one sample and enforce storage limit."""
    cfg = config_store.get().persistence
    if not cfg.enabled:
        return
    async with async_session_factory() as session:
        row = Sample(**_live_to_row(data))
        session.add(row)
        await session.commit()
    await enforce_storage_limit()


def _target_rows_for_mb(mb: float) -> int:
    """Approximate max rows to stay under mb (for rollover)."""
    return int(mb * 1024 * 1024 / BYTES_PER_ROW)


async def enforce_storage_limit() -> None:
    """If DB exceeds config (size or age), delete oldest rows; then VACUUM to reclaim space."""
    cfg = config_store.get().persistence
    db_path = settings.data_dir / "history.db"
    if not db_path.exists():
        return
    async with async_session_factory() as session:
        if cfg.rollover_strategy == "keep_days" and cfg.keep_days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=cfg.keep_days)
            await session.execute(delete(Sample).where(Sample.timestamp_utc < cutoff))
            await session.commit()
        # Enforce size limit by row count (file won't shrink until VACUUM)
        target = _target_rows_for_mb(cfg.max_storage_mb)
        result = await session.execute(select(func.count()).select_from(Sample))
        count = result.scalar() or 0
        while count > target:
            result = await session.execute(
                select(Sample.id).order_by(Sample.timestamp_utc.asc()).limit(500)
            )
            ids = [r[0] for r in result.fetchall()]
            if not ids:
                break
            await session.execute(delete(Sample).where(Sample.id.in_(ids)))
            await session.commit()
            count -= len(ids)
    # Reclaim file space (VACUUM can be slow; run only when we've deleted)
    size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
    if size_mb > cfg.max_storage_mb:
        try:
            async with async_session_factory() as session:
                await session.execute(text("VACUUM"))
                await session.commit()
        except Exception:
            pass  # VACUUM may fail under load; rollover still applied


def get_db_size_mb() -> float:
    """Current size of history DB file in MB."""
    p = settings.data_dir / "history.db"
    return p.stat().st_size / (1024 * 1024) if p.exists() else 0.0


def get_disk_available_mb() -> Optional[float]:
    """Available disk space on the volume containing the data dir (MB)."""
    try:
        usage = shutil.disk_usage(settings.data_dir)
        return usage.free / (1024 * 1024)
    except OSError:
        return None


async def get_row_count() -> int:
    """Total number of samples in the DB."""
    async with async_session_factory() as session:
        result = await session.execute(select(func.count()).select_from(Sample))
        return result.scalar() or 0


async def get_storage_info() -> dict:
    """Aggregate storage info for the UI: disk available, DB size, row count, config."""
    cfg = config_store.get().persistence
    disk_mb = get_disk_available_mb()
    db_mb = get_db_size_mb()
    rows = await get_row_count()
    return {
        "disk_available_mb": round(disk_mb, 2) if disk_mb is not None else None,
        "db_size_mb": round(db_mb, 2),
        "row_count": rows,
        "config": cfg.model_dump(),
    }


async def get_latest_sample() -> Optional[LiveData]:
    """Return the most recent sample as LiveData, for display when no inverter is connected."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(Sample).order_by(Sample.timestamp_utc.desc()).limit(1)
        )
        row = result.scalars().first()
    if not row:
        return None
    return LiveData(
        timestamp=row.timestamp_utc,
        pv_power_w=row.pv_power_w,
        pv_voltage_v=row.pv_voltage_v,
        pv_current_a=row.pv_current_a,
        battery_soc_percent=row.battery_soc_percent,
        battery_power_w=row.battery_power_w,
        battery_voltage_v=row.battery_voltage_v,
        battery_current_a=row.battery_current_a,
        battery_temperature_c=row.battery_temperature_c,
        grid_power_w=row.grid_power_w,
        grid_voltage_v=row.grid_voltage_v,
        grid_frequency_hz=row.grid_frequency_hz,
        load_power_w=row.load_power_w,
        inverter_temperature_c=row.inverter_temperature_c,
        status_message=row.status_message or "",
        mode=row.mode or "",
    )


async def get_history(
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    limit: int = 1000,
) -> list[dict]:
    """Return samples for charts. Default: latest `limit` rows."""
    async with async_session_factory() as session:
        q = select(Sample).order_by(Sample.timestamp_utc.desc()).limit(limit)
        if from_ts is not None:
            q = q.where(Sample.timestamp_utc >= from_ts)
        if to_ts is not None:
            q = q.where(Sample.timestamp_utc <= to_ts)
        result = await session.execute(q)
        samples = result.scalars().all()
    return [
        {
            "timestamp": s.timestamp_utc.isoformat(),
            "pv_power_w": s.pv_power_w,
            "battery_soc_percent": s.battery_soc_percent,
            "battery_power_w": s.battery_power_w,
            "grid_power_w": s.grid_power_w,
            "load_power_w": s.load_power_w,
        }
        for s in reversed(samples)
    ]
