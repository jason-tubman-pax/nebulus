"""Registry of inverter drivers by name."""
from typing import Optional

from app.models.settings import InverterConnectionConfig

from app.drivers.base import BaseInverterDriver
from app.drivers.deye import DeyeDriver
from app.drivers.generic import GenericModbusDriver
from app.drivers.sofar import SofarDriver

_DRIVERS: dict[str, type[BaseInverterDriver]] = {
    "deye": DeyeDriver,
    "sofar": SofarDriver,
    "generic": GenericModbusDriver,
}

# Solar Assistant–style display names for UI
DRIVER_DISPLAY_NAMES: dict[str, str] = {
    "deye": "Deye",
    "generic": "Generic Modbus",
    "sofar": "Sofar",
    "growatt": "Growatt",
    "luxpower": "Luxpower",
    "victron": "Victron",
    "pylontech": "Pylontech (BMS)",
    "byd": "BYD",
    "solax": "Solax",
    "solaredge": "SolarEdge",
}


def get_driver(config: InverterConnectionConfig) -> BaseInverterDriver:
    """Instantiate driver for given config."""
    name = (config.driver or "generic").lower()
    cls = _DRIVERS.get(name, GenericModbusDriver)
    return cls(config)


def list_drivers() -> dict[str, str]:
    """Return driver id -> display name for UI dropdown."""
    out = {}
    for name, cls in _DRIVERS.items():
        out[name] = cls.display_name
    return out
