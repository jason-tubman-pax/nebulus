"""Storage and history API: disk usage, limits, rollover config, history for charts."""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.models.settings import PersistenceConfig
from app.services.config_store import config_store
from app.services import history_service

router = APIRouter()


@router.get("/storage")
async def get_storage() -> dict[str, Any]:
    """Current storage usage, disk available, row count, and persistence config."""
    return await history_service.get_storage_info()


@router.put("/storage/config", response_model=PersistenceConfig)
def update_storage_config(config: PersistenceConfig) -> PersistenceConfig:
    """Update persistence (max size, interval, rollover). UI should cap max_storage_mb at disk_available_mb."""
    cfg = config_store.get()
    cfg.persistence = config
    config_store.set(cfg)
    return config_store.get().persistence


@router.get("/history")
async def get_history(
    from_ts: Optional[datetime] = Query(None, description="Start time (ISO)"),
    to_ts: Optional[datetime] = Query(None, description="End time (ISO)"),
    limit: int = Query(1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    """Samples for charts. Default: latest `limit` rows."""
    return await history_service.get_history(from_ts=from_ts, to_ts=to_ts, limit=limit)
