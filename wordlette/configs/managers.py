import logging
from pathlib import Path
from typing import Type, TypeVar, Any, Callable, Iterable, BinaryIO

from wordlette.configs.exceptions import ConfigCannotCreateFiles
from wordlette.configs.handlers import ConfigHandler
from wordlette.core.exceptions import ConfigFileNotFound

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Config")
T = TypeVar("T")


class ConfigManager:
    def __init__(self, handlers: Iterable[Type[ConfigHandler]] = ()):
        self._handler_extensions: dict[str, ConfigHandler] = {}
        self._handlers: list[ConfigHandler] = []
        self._config: dict[str, Any] = {}

        self._register_handlers(handlers)

    @property
    def valid_extensions(self) -> set[str]:
        return set(self._handler_extensions.keys())

    def get(
        self, key: str = "", constructor: Callable[[dict[str, Any]], T] | None = None
    ) -> T | Any:
        value = self._config[key] if key else self._config
        if constructor:
            value = constructor(**value)

        return value

    def find_config_file(self, name: str, directory: Path) -> Path | None:
        for extension in self._handler_extensions:
            path = directory / f"{name}.{extension}"
            if path.exists():
                return path

    def load_config_file(self, name: str, directory: Path):
        path = self.find_config_file(name, directory)
        if not path:
            raise ConfigFileNotFound(
                f"Could not find any config files that matched the naming scheme '{name}.*' in '{directory}'."
            )

        handler = self._handler_extensions[path.suffix[1:].casefold()]
        with path.open("rb") as open_file:
            self._config = handler.load(open_file)

        logger.debug(f"Loaded config file '{path}'.")

    def write_config_file(self, name: str, directory: Path, data: T) -> Path:
        if path := self.find_config_file(name, directory):
            logger.debug(f"Found existing config file {str(path)!r}.")
            with path.open("wb") as open_file:
                self._write_file_with_handler(
                    data,
                    open_file,
                    self._handler_extensions[path.suffix[1:].casefold()],
                )

        else:
            path = directory / f"{name}.tmp"
            with path.open("wb") as open_file:
                for handler in self._handlers:
                    logger.debug(
                        f"Attempting to create config using {type(handler).__name__}."
                    )
                    try:
                        self._write_file_with_handler(data, open_file, handler)
                    except ConfigCannotCreateFiles:
                        open_file.truncate()
                        continue
                    else:
                        extension = min(handler.extensions)
                        new_name = f"{name}.{extension}"
                        path.rename(new_name)
                        path = directory / new_name
                        break

        logger.debug(f"Wrote to config file {str(path)!r}.")

        self._config = data
        return path

    def _write_file_with_handler(
        self, data: dict[str, Any], file: BinaryIO, handler: ConfigHandler
    ):
        handler.write(data, file)

    def add_handler(self, handler_type: Type[ConfigHandler]):
        self._handlers.append(handler := handler_type())
        for extension in handler.extensions:
            self._handler_extensions[extension.casefold()] = handler

    def remove_handler(self, handler: Type[ConfigHandler]):
        for extension in handler.extensions:
            del self._handler_extensions[extension.casefold()]

    def _register_handlers(self, handlers: Iterable[Type[ConfigHandler]]):
        for handler in handlers:
            self.add_handler(handler)
