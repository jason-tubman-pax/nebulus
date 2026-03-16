"""Base class for inverter/battery Modbus drivers."""
from abc import ABC, abstractmethod
from typing import Optional

from app.models.live import LiveData
from app.models.settings import InverterConnectionConfig, InverterSettings


class DriverCapability:
    """Flags for what a driver supports."""
    READ_LIVE = "read_live"
    READ_SETTINGS = "read_settings"
    WRITE_SETTINGS = "write_settings"


class BaseInverterDriver(ABC):
    """Abstract inverter driver. Each manufacturer implements this."""

    name: str = "base"
    display_name: str = "Generic"
    capabilities: set[str] = frozenset()

    def __init__(self, config: InverterConnectionConfig) -> None:
        self.config = config
        self._client = None

    @abstractmethod
    def connect(self) -> bool:
        """Open Modbus connection. Return True on success."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection."""
        ...

    @abstractmethod
    def read_live_data(self) -> Optional[LiveData]:
        """Read current registers and return LiveData. Return None on error."""
        ...

    def read_settings(self) -> Optional[InverterSettings]:
        """Read current setpoints. Default: not implemented."""
        return None

    def write_settings(self, settings: InverterSettings) -> bool:
        """Apply setpoints. Default: not implemented."""
        return False

    def is_connected(self) -> bool:
        return self._client is not None
