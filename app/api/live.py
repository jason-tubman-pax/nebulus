"""Live data and WebSocket for real-time dashboard."""
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.live import LiveData
from app.services.modbus_service import modbus_service

router = APIRouter()


@router.get("/live", response_model=Optional[LiveData])
def get_live() -> Optional[LiveData]:
    """Current snapshot (polling fallback)."""
    return modbus_service.get_latest()


@router.websocket("/live/ws")
async def websocket_live(websocket: WebSocket) -> None:
    """Stream live data as JSON whenever the Modbus service updates."""
    await websocket.accept()
    queue = modbus_service.subscribe()
    try:
        # Send latest immediately if available
        latest = modbus_service.get_latest()
        if latest:
            await websocket.send_json(latest.model_dump(mode="json"))
        while True:
            data: LiveData = await asyncio.wait_for(queue.get(), timeout=30.0)
            await websocket.send_json(data.model_dump(mode="json"))
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        modbus_service.unsubscribe(queue)
