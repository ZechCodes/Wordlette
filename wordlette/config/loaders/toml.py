from pathlib import Path
from typing import Any

from .base import FileTypeLoader


try:
    import tomli

    toml_installed = True
except ImportError:
    tomli = False
    toml_installed = False


class TomlFileLoader(FileTypeLoader):
    def __init__(self, config_path: Path, file_name: str):
        self._file_path = config_path / f"{file_name}.toml"

    @property
    def file_path(self) -> Path:
        return self._file_path

    def exists(self) -> bool:
        return tomli and self.file_path.exists()

    def load(self) -> dict[str, Any]:
        with self.file_path.open("b") as file:
            return tomli.load(file)
