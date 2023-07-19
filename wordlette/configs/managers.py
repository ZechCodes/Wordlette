from pathlib import Path
from typing import Type, Sequence, TypeVar, Any, Callable

from wordlette.configs.handlers import ConfigHandler

T = TypeVar("T")


class Config:
    def __init__(self, path: Path, data: dict[str, Any]):
        self.path = path
        self.data = data


class ConfigManager:
    def __init__(self, handlers: Sequence[Type[ConfigHandler]] = ()):
        self._handlers: dict[str, ConfigHandler] = {}
        self._config: Config | None = None

        self._register_handlers(handlers)

    def get(
        self, key: str = "", constructor: Callable[[dict[str, Any]], T] | None = None
    ) -> T | Any:
        value = self._config.data[key] if key else self._config.data
        if constructor:
            value = constructor(value)

        return value

    def find_config_file(self, name: str, directory: Path) -> Path | None:
        if self._config is not None:
            return self._config.path

        for extension in self._handlers:
            path = directory / f"{name}.{extension}"
            if path.exists():
                return path

    def load_config_file(self, name: str, directory: Path):
        for extension, handler in self._handlers.items():
            file = directory / f"{name}.{extension}"
            if file.exists():
                with file.open("rb") as open_file:
                    self._config = Config(file, handler.load(open_file))

    def write_config_file(self, name: str, directory: Path, data: T):
        if path := self.find_config_file(name, directory):
            handler = self._handlers[path.suffix[1:].casefold()]
        else:
            extension = list(self._handlers)[0]
            handler = self._handlers[extension]
            path = directory / f"{name}.{extension}"

        self._config = Config(path, data)
        with path.open("wb") as open_file:
            handler.write(data, open_file)

    def add_handler(self, handler: Type[ConfigHandler]):
        for extension in handler.extensions:
            self._handlers[extension.casefold()] = handler()

    def remove_handler(self, handler: Type[ConfigHandler]):
        for extension in handler.extensions:
            del self._handlers[extension.casefold()]

    def _register_handlers(self, handlers: Sequence[Type[ConfigHandler]]):
        for handler in handlers:
            self.add_handler(handler)
