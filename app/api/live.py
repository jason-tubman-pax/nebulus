"""Live data and WebSocket for real-time dashboard."""
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.live import LiveData
from app.services.modbus_service import modbus_service
from app.services import history_service

router = APIRouter()


@router.get("/live", response_model=Optional[LiveData])
async def get_live() -> Optional[LiveData]:
    """Current snapshot: from Modbus when connected, else latest from history (e.g. seeded data)."""
    latest = modbus_service.get_latest()
    if latest is not None:
        return latest
    return await history_service.get_latest_sample()


@router.websocket("/live/ws")
async def websocket_live(websocket: WebSocket) -> None:
    """Stream live data as JSON whenever the Modbus service updates. Sends latest from history if no inverter."""
    await websocket.accept()
    queue = modbus_service.subscribe()
    try:
        # Send latest immediately: Modbus first, else fall back to latest from history (e.g. seeded)
        latest = modbus_service.get_latest()
        if latest is None:
            latest = await history_service.get_latest_sample()
        if latest:
            await websocket.send_json(latest.model_dump(mode="json"))
        while True:
            data: LiveData = await asyncio.wait_for(queue.get(), timeout=30.0)
            await websocket.send_json(data.model_dump(mode="json"))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        modbus_service.unsubscribe(queue)
