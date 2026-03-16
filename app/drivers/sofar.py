"""Sofar hybrid inverter Modbus driver (placeholder for full implementation)."""
from datetime import datetime
from typing import Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient

from app.drivers.base import BaseInverterDriver, DriverCapability
from app.models.live import LiveData
from app.models.settings import InverterConnectionConfig, InverterSettings


class SofarDriver(BaseInverterDriver):
    """Sofar HYD series. Register map to be completed from manufacturer/community docs."""

    name = "sofar"
    display_name = "Sofar"
    capabilities = {DriverCapability.READ_LIVE}

    def __init__(self, config: InverterConnectionConfig) -> None:
        super().__init__(config)
        self._client = None

    def connect(self) -> bool:
        try:
            cfg = self.config
            if cfg.connection_type == "tcp" and cfg.host:
                self._client = ModbusTcpClient(
                    host=cfg.host,
                    port=cfg.port,
                    timeout=cfg.timeout_seconds,
                )
            elif cfg.connection_type == "rtu" and cfg.serial_port:
                self._client = ModbusSerialClient(
                    port=cfg.serial_port,
                    baudrate=cfg.baudrate,
                    timeout=cfg.timeout_seconds,
                )
            else:
                return False
            return self._client.connect()
        except Exception:
            return False

    def disconnect(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def read_live_data(self) -> Optional[LiveData]:
        if not self._client or not self._client.connected:
            if not self.connect():
                return None
        # TODO: Sofar register map - add registers from docs
        return LiveData(
            timestamp=datetime.utcnow(),
            status_message="Sofar (placeholder)",
        )
