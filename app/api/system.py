"""System and inverter configuration."""
from fastapi import APIRouter, HTTPException

from app.models.settings import (
    SystemConfig,
    InverterConnectionConfig,
    InverterSettings,
)
from app.services.config_store import config_store
from app.drivers.registry import list_drivers

router = APIRouter()


@router.get("/config", response_model=SystemConfig)
def get_config() -> SystemConfig:
    return config_store.get()


@router.put("/config", response_model=SystemConfig)
def put_config(config: SystemConfig) -> SystemConfig:
    config_store.set(config)
    return config_store.get()


@router.get("/inverter/drivers")
def get_inverter_drivers() -> dict[str, str]:
    """List available inverter drivers for UI dropdown."""
    return list_drivers()


@router.put("/inverter/connection", response_model=SystemConfig)
def update_inverter_connection(conn: InverterConnectionConfig) -> SystemConfig:
    cfg = config_store.get()
    cfg.inverter = conn
    config_store.set(cfg)
    return config_store.get()


@router.put("/inverter/settings", response_model=SystemConfig)
def update_inverter_settings(settings_payload: InverterSettings) -> SystemConfig:
    cfg = config_store.get()
    cfg.inverter_settings = settings_payload
    config_store.set(cfg)
    # Optionally push to device via driver
    # driver = get_driver(cfg.inverter); driver.connect(); driver.write_settings(settings_payload)
    return config_store.get()


@router.post("/inverter/settings/apply")
def apply_inverter_settings() -> dict:
    """Apply current inverter_settings to the device via Modbus."""
    from app.drivers.registry import get_driver
    cfg = config_store.get()
    driver = get_driver(cfg.inverter)
    if not driver.connect():
        raise HTTPException(status_code=503, detail="Could not connect to inverter")
    try:
        ok = driver.write_settings(cfg.inverter_settings)
        return {"success": ok}
    finally:
        driver.disconnect()
