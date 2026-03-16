"""Background Modbus polling and live data broadcast."""
import asyncio
from typing import Optional

from app.core.config import settings
from app.models.live import LiveData
from app.services.config_store import config_store
from app.services import history_service
from app.drivers.registry import get_driver


class ModbusService:
    """Polls inverter via active driver and keeps latest LiveData for WebSocket."""

    def __init__(self) -> None:
        self._latest: Optional[LiveData] = None
        self._task: Optional[asyncio.Task] = None
        self._subscribers: set[asyncio.Queue] = set()
        self._last_save_monotonic: float = 0.0

    def get_latest(self) -> Optional[LiveData]:
        return self._latest

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def _broadcast(self, data: LiveData) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass

    async def _poll_loop(self) -> None:
        interval = settings.modbus_poll_interval_seconds
        while True:
            try:
                cfg = config_store.get()
                driver = get_driver(cfg.inverter)
                if driver.connect():
                    data = driver.read_live_data()
                    driver.disconnect()
                    if data:
                        self._latest = data
                        await self._broadcast(data)
                        # Persist at configured sample interval (respects storage limit)
                        if cfg.persistence.enabled and cfg.persistence.sample_interval_seconds > 0:
                            now = asyncio.get_event_loop().time()
                            if now - self._last_save_monotonic >= cfg.persistence.sample_interval_seconds:
                                self._last_save_monotonic = now
                                try:
                                    await history_service.save_sample(data)
                                except Exception:
                                    pass
            except Exception:
                pass
            await asyncio.sleep(interval)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._poll_loop())

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


modbus_service = ModbusService()
