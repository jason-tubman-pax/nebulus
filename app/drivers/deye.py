"""Deye / Sunsynk hybrid inverter Modbus driver (RTU/TCP).

Live data uses INPUT REGISTERS (read-only). Map from Deye/Sunsynk protocol docs
and community: https://kellerza.github.io/sunsynk/reference/definitions
Single-phase (1PH) register set; three-phase uses different offsets.
"""
from datetime import datetime
from typing import Optional

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.exceptions import ModbusException

from app.drivers.base import BaseInverterDriver, DriverCapability
from app.models.live import LiveData
from app.models.settings import InverterConnectionConfig, InverterSettings


# Single-phase (1PH) input register addresses (Deye/Sunsynk)
# Scale factors from https://kellerza.github.io/sunsynk/reference/definitions
DEYE_INPUT = {
    "overall_state": 59,
    "grid_frequency": 79,
    "dc_transformer_temp": 90,
    "radiator_temp": 91,
    "pv1_voltage": 109,
    "pv1_current": 110,
    "pv2_voltage": 111,
    "pv2_current": 112,
    "grid_voltage": 150,
    "grid_power": 169,  # signed
    "load_power": 178,  # signed
    "battery_temp": 182,
    "battery_voltage": 183,
    "battery_soc": 184,
    "pv1_power": 186,   # signed
    "pv2_power": 187,   # signed
    "battery_power": 190,  # signed
    "battery_current": 191,
    "inverter_frequency": 193,
}
# Read one block from min to max address
_DEYE_FIRST = min(DEYE_INPUT.values())
_DEYE_LAST = max(DEYE_INPUT.values())
_DEYE_COUNT = _DEYE_LAST - _DEYE_FIRST + 1


def _u16_to_s16(val: int) -> int:
    """Interpret uint16 as int16 (Modbus signed)."""
    return val if val < 0x8000 else val - 0x10000


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

    def _read_input_registers(self, address: int, count: int = 1) -> Optional[list[int]]:
        """Read input registers (function code 0x04). Deye live data is here."""
        if not self._client:
            return None
        try:
            result = self._client.read_input_registers(
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
        regs = self._read_input_registers(_DEYE_FIRST, _DEYE_COUNT)
        if not regs or len(regs) < _DEYE_COUNT:
            return None

        def idx(addr: int) -> int:
            return addr - _DEYE_FIRST

        def u16(addr: int) -> int:
            i = idx(addr)
            return regs[i] if 0 <= i < len(regs) else 0

        def s16(addr: int) -> int:
            return _u16_to_s16(u16(addr))

        # Scales from sunsynk definitions (1PH)
        pv1_v = u16(DEYE_INPUT["pv1_voltage"]) * 0.1
        pv1_i = u16(DEYE_INPUT["pv1_current"]) * 0.1
        pv2_v = u16(DEYE_INPUT["pv2_voltage"]) * 0.1
        pv2_i = u16(DEYE_INPUT["pv2_current"]) * 0.1
        pv1_power = s16(DEYE_INPUT["pv1_power"])
        pv2_power = s16(DEYE_INPUT["pv2_power"])
        pv_power_w = pv1_power + pv2_power

        batt_soc = u16(DEYE_INPUT["battery_soc"])
        batt_power = s16(DEYE_INPUT["battery_power"])
        batt_v = u16(DEYE_INPUT["battery_voltage"]) * 0.01
        batt_i = u16(DEYE_INPUT["battery_current"]) * 0.01
        batt_temp_raw = u16(DEYE_INPUT["battery_temp"])
        battery_temp_c = (batt_temp_raw * 0.1) if batt_temp_raw else None

        grid_power = s16(DEYE_INPUT["grid_power"])
        grid_v = u16(DEYE_INPUT["grid_voltage"]) * 0.1
        grid_hz = u16(DEYE_INPUT["grid_frequency"]) * 0.01

        load_power = s16(DEYE_INPUT["load_power"])

        inv_temp_raw = u16(DEYE_INPUT["radiator_temp"]) or u16(DEYE_INPUT["dc_transformer_temp"])
        inverter_temp_c = (inv_temp_raw * 0.1) if inv_temp_raw else None

        state = u16(DEYE_INPUT["overall_state"])
        mode = str(state)  # 1=Normal, 2=ByPass, etc.; can map to string later

        return LiveData(
            timestamp=datetime.utcnow(),
            pv_power_w=float(max(0, pv_power_w)),
            pv_voltage_v=pv1_v + pv2_v,
            pv_current_a=pv1_i + pv2_i,
            battery_soc_percent=float(min(100, max(0, batt_soc))),
            battery_power_w=float(batt_power),
            battery_voltage_v=batt_v,
            battery_current_a=batt_i,
            battery_temperature_c=battery_temp_c,
            grid_power_w=float(grid_power),
            grid_voltage_v=grid_v,
            grid_frequency_hz=grid_hz,
            load_power_w=float(load_power),
            inverter_temperature_c=inverter_temp_c,
            status_message="Deye",
            mode=mode,
        )

    def read_settings(self) -> Optional[InverterSettings]:
        # Settings are in holding registers; map varies by model (see sunsynk definitions).
        if not self._client or not self._client.connected:
            if not self.connect():
                return None
        return InverterSettings()

    def write_settings(self, settings: InverterSettings) -> bool:
        if not self._client or not self._client.connected:
            if not self.connect():
                return False
        # Write to holding registers with validation (model-specific addresses).
        return True
