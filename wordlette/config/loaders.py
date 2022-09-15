from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class FileTypeLoader(ABC):
    @abstractmethod
    def __init__(self, config_path: Path, file_name: str):
        ...

    @property
    @abstractmethod
    def file_path(self) -> Path:
        ...

    @abstractmethod
    def exists(self) -> bool:
        ...

    @abstractmethod
    def load(self) -> dict[str, Any]:
        ...
