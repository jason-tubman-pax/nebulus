"""In-memory + file persistence for system config."""
import json
from pathlib import Path
from typing import Optional

from app.models.settings import SystemConfig
from app.core.config import settings


class ConfigStore:
    """Load/save SystemConfig to JSON file."""

    def __init__(self) -> None:
        self._config: Optional[SystemConfig] = None

    def get(self) -> SystemConfig:
        if self._config is None:
            self._config = self._load()
        return self._config

    def set(self, config: SystemConfig) -> None:
        self._config = config
        self._save()

    def _path(self) -> Path:
        p = settings.config_path
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def _load(self) -> SystemConfig:
        path = self._path()
        if not path.exists():
            return SystemConfig()
        try:
            data = json.loads(path.read_text())
            return SystemConfig.model_validate(data)
        except Exception:
            return SystemConfig()

    def _save(self) -> None:
        if self._config is None:
            return
        path = self._path()
        path.write_text(self._config.model_dump_json(indent=2))


config_store = ConfigStore()
