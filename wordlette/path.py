import bevy
import importlib.util
import pathlib
from typing import Optional
from types import ModuleType


class Path(bevy.Bevy):
    def __init__(self):
        self._path: Optional[pathlib.Path] = None

    @property
    def package(self) -> str:
        return self.path.name

    @property
    def path(self) -> Optional[pathlib.Path]:
        return self._path

    @path.setter
    def path(self, path: str):
        if self.path:
            raise ValueError("Cannot set the path once it has already been set")

        self._path = pathlib.Path(path).parent

        if not self._path.exists():
            raise FileNotFoundError(f"Could not find {self._path.resolve()}")

    def build_path(self, name: str, /, *, extension: Optional[str] = None) -> pathlib.Path:
        if not self.path:
            raise ValueError("No path is set")

        directories = name.split(".")
        if extension:
            file = directories.pop()

        path = self.path
        for name in directories:
            path = path / name

        if extension:
            path = path / f"{file}.toml"

        return path

    def importer(self, module_name: str) -> Optional[ModuleType]:
        full_name = f"{self.package}.{module_name}"
        spec = importlib.util.find_spec(full_name)
        if spec:
            return spec.loader.load_module()
        return None
