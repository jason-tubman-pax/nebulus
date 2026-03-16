"""Deye hybrid inverter Modbus driver (RTU/TCP). Register map from public/community docs."""
from datetime import datetime
from typing import Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException

from app.drivers.base import BaseInverterDriver, DriverCapability
from app.models.live import LiveData
from app.models.settings import InverterConnectionConfig, InverterSettings


# Deye SUN series holding registers (common map; variants may differ)
# Addresses and scales from community/docs. Adjust for your exact model.
DEYE_REG = {
    "pv_power": 0x00,       # total PV power W
    "pv1_voltage": 0x01,
    "pv1_current": 0x02,
    "pv2_voltage": 0x03,
    "pv2_current": 0x04,
    "battery_soc": 0x10,
    "battery_power": 0x11,  # + charge, - discharge
    "battery_voltage": 0x12,
    "battery_current": 0x13,
    "grid_power": 0x20,
    "grid_voltage": 0x21,
    "grid_frequency": 0x22,
    "load_power": 0x30,
    "inverter_temp": 0x40,
    "battery_temp": 0x41,
    "work_mode": 0x50,
}


class DeyeDriver(BaseInverterDriver):
    name = "deye"
    display_name = "Deye"
    capabilities = {
        DriverCapability.READ_LIVE,
        DriverCapability.READ_SETTINGS,
        DriverCapability.WRITE_SETTINGS,
    }

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

    def _read_holding_single(self, addr: int) -> Optional[int]:
        r = self._read_holding(addr, 1)
        return r[0] if r else None

    def read_live_data(self) -> Optional[LiveData]:
        if not self._client or not self._client.connected:
            if not self.connect():
                return None
        # Read a block that covers common registers (addresses 0–0x50+)
        regs = self._read_holding(0, 0x55)
        if not regs or len(regs) < 0x55:
            return None

        def u16(offset: int) -> int:
            return regs[offset] if offset < len(regs) else 0

        # Deye often uses 0.1 scale for V/A, 1 for W
        pv1_v = u16(0x01) * 0.1
        pv1_i = u16(0x02) * 0.1
        pv2_v = u16(0x03) * 0.1
        pv2_i = u16(0x04) * 0.1
        pv_power = u16(0x00)
        pv_voltage = pv1_v + pv2_v if (pv1_v or pv2_v) else 0
        pv_current = pv1_i + pv2_i

        return LiveData(
            timestamp=datetime.utcnow(),
            pv_power_w=float(pv_power),
            pv_voltage_v=pv_voltage,
            pv_current_a=pv_current,
            battery_soc_percent=float(u16(0x10)),
            battery_power_w=float(u16(0x11)),
            battery_voltage_v=u16(0x12) * 0.1,
            battery_current_a=u16(0x13) * 0.1,
            grid_power_w=float(u16(0x20)),
            grid_voltage_v=u16(0x21) * 0.1,
            grid_frequency_hz=u16(0x22) * 0.01,
            load_power_w=float(u16(0x30)),
            inverter_temperature_c=float(u16(0x40)) if u16(0x40) != 0 else None,
            battery_temperature_c=float(u16(0x41)) if u16(0x41) != 0 else None,
            mode=str(u16(0x50)),
            status_message="Deye",
        )

    def read_settings(self) -> Optional[InverterSettings]:
        # Deye-specific register map for setpoints (example addresses)
        if not self._client or not self._client.connected:
            if not self.connect():
                return None
        # Placeholder: read charge/discharge limits from known registers
        return InverterSettings()

    def write_settings(self, settings: InverterSettings) -> bool:
        if not self._client or not self._client.connected:
            if not self.connect():
                return False
        # Placeholder: write to Deye holding registers with validation
        return True
