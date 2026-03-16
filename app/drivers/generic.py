"""Generic Modbus driver: reads a minimal common register set (for testing/unknown inverters)."""
from datetime import datetime
from typing import Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException

from app.drivers.base import BaseInverterDriver, DriverCapability
from app.models.live import LiveData
from app.models.settings import InverterConnectionConfig, InverterSettings


# Generic holding registers often used across brands (adjust to your hardware)
# These are example addresses; real maps vary by inverter.
GENERIC_REGISTERS = {
    "pv_power": 0,
    "battery_soc": 1,
    "battery_power": 2,
    "grid_power": 3,
    "load_power": 4,
}


class GenericModbusDriver(BaseInverterDriver):
    name = "generic"
    display_name = "Generic Modbus"
    capabilities = {DriverCapability.READ_LIVE}

    def __init__(self, config: InverterConnectionConfig) -> None:
        super().__init__(config)
        self._client = None

    def connect(self) -> bool:
        try:
            if self.config.connection_type == "tcp" and self.config.host:
                self._client = ModbusTcpClient(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout_seconds,
                )
            elif self.config.connection_type == "rtu" and self.config.serial_port:
                self._client = ModbusSerialClient(
                    port=self.config.serial_port,
                    baudrate=self.config.baudrate,
                    timeout=self.config.timeout_seconds,
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

    def _read_holding(self, address: int, count: int = 1) -> Optional[list[int]]:
        if not self._client:
            return None
        try:
            result = self._client.read_holding_registers(
                address, count, slave=self.config.slave_id
            )
            if result.isError():
                return None
            return result.registers
        except (ModbusException, Exception):
            return None

    def read_live_data(self) -> Optional[LiveData]:
        if not self._client or not self._client.connected:
            if not self.connect():
                return None
        regs = self._read_holding(0, 20)
        if not regs:
            return None
        # Map first few registers to LiveData (scale factors are device-specific)
        return LiveData(
            timestamp=datetime.utcnow(),
            pv_power_w=float(regs[0] if len(regs) > 0 else 0),
            battery_soc_percent=float(regs[1] if len(regs) > 1 else 0),
            battery_power_w=float(regs[2] if len(regs) > 2 else 0),
            grid_power_w=float(regs[3] if len(regs) > 3 else 0),
            load_power_w=float(regs[4] if len(regs) > 4 else 0),
            status_message="Generic driver",
        )
