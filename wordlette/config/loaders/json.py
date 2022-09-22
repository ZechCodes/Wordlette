import json
from pathlib import Path
from typing import Any

from .base import FileTypeLoader

json_installed = True


class JsonFileLoader(FileTypeLoader):
    def __init__(self, config_path: Path, file_name: str):
        self._file_path = config_path / f"{file_name}.json"

    @property
    def file_path(self) -> Path:
        return self._file_path

    def exists(self) -> bool:
        return self.file_path.exists()

    def load(self) -> dict[str, Any]:
        with self.file_path.open() as file:
            return json.load(file)
