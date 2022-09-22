from functools import cache
from pathlib import Path
from typing import Any

from .base import FileTypeLoader


try:
    import yaml

    yaml_installed = True
except ImportError:
    yaml = False
    yaml_installed = False


class YamlFileLoader(FileTypeLoader):
    def __init__(self, config_path: Path, file_name: str):
        self._config_path = config_path
        self._file_name = file_name

    @property
    @cache
    def file_path(self) -> Path:
        path = self._config_path / f"{self._file_name}.yaml"
        if path.exists():
            return path

        return self._config_path / f"{self._file_name}.yml"

    def exists(self) -> bool:
        return yaml and self.file_path.exists()

    def load(self) -> dict[str, Any]:
        with self.file_path.open() as file:
            return yaml.safe_load(file)
