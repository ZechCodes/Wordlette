from collections import UserDict
from pathlib import Path
from typing import Any, Type, TypeVar

from bevy import Bevy, bevy_method, Inject

from wordlette import Logging
from wordlette.settings import Settings
from .loaders.base import FileTypeLoader


M = TypeVar("M")


class ConfigFile:
    def __init__(self, file_path: Path, data: dict[str, Any]):
        self._path = file_path
        self._data = data

    def populate_model(self, model_type: Type[M] = dict, section: str = "") -> M | None:
        if not section:
            section = model_type.__config_table__

        if section in self._data:
            data = self._data[section]
            if issubclass(model_type, dict | UserDict):
                return data

            return model_type(**data)

        return None


class Config(Bevy):
    def __init__(self):
        self._config_files: list[ConfigFile] = []

    @property
    def found_config_files(self) -> bool:
        return bool(self._config_files)

    def populate_model(
        self, model_type: Type[M], section: str = "", allow_empty: bool = True
    ) -> M | None:
        for file in self._config_files:
            if model := file.populate_model(model_type, section):
                return model

        return model_type() if allow_empty else None

    @bevy_method
    async def load_config(self, settings: Settings = Inject):
        if settings.get("dev", True):
            await self._load_config_file("site-config.dev")

        await self._load_config_file("site-config")

    @bevy_method
    async def _load_config_file(
        self,
        file_name: str,
        settings: Settings = Inject,
        log: Logging["config"] = Inject,
    ):
        config_path: Path = settings.get("config_path", Path().resolve())
        file_loaders: list[Type[FileTypeLoader]] = settings.get("file_loaders", [])
        for file_loader in file_loaders:
            if (loader := file_loader(config_path, file_name)).exists():
                self._config_files.append(ConfigFile(loader.file_path, loader.load()))
                log.debug(f"Loaded {loader.file_path}")
