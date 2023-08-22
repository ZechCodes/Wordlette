import logging
from pathlib import Path
from typing import Type, Sequence, TypeVar, Any, Callable

from wordlette.configs.handlers import ConfigHandler
from wordlette.core.exceptions import ConfigFileNotFound

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Config")
T = TypeVar("T")


class ConfigManager:
    def __init__(self, handlers: Sequence[Type[ConfigHandler]] = ()):
        self._handlers: dict[str, ConfigHandler] = {}
        self._config: dict[str, Any] = {}

        self._register_handlers(handlers)

    @property
    def valid_extensions(self) -> set[str]:
        return set(self._handlers.keys())

    def get(
        self, key: str = "", constructor: Callable[[dict[str, Any]], T] | None = None
    ) -> T | Any:
        value = self._config[key] if key else self._config
        if constructor:
            value = constructor(**value)

        return value

    def find_config_file(self, name: str, directory: Path) -> Path | None:
        for extension in self._handlers:
            path = directory / f"{name}.{extension}"
            if path.exists():
                return path

    def load_config_file(self, name: str, directory: Path):
        path = self.find_config_file(name, directory)
        if not path:
            raise ConfigFileNotFound(
                f"Could not find any config files that matched the naming scheme '{name}.*' in '{directory}'."
            )

        handler = self._handlers[path.suffix[1:].casefold()]
        with path.open("rb") as open_file:
            self._config = handler.load(open_file)

        logger.debug(f"Loaded config file '{path}'.")

    def write_config_file(self, name: str, directory: Path, data: T):
        if path := self.find_config_file(name, directory):
            handler = self._handlers[path.suffix[1:].casefold()]
        else:
            extension = list(self._handlers)[0]
            handler = self._handlers[extension]
            path = directory / f"{name}.{extension}"

        self._config = data
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
