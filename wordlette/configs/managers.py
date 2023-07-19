from typing import Type, Sequence, TypeVar, Any, Callable
from wordlette.configs.handlers import ConfigHandler
class ConfigManager:
    def __init__(self, handlers: Sequence[Type[ConfigHandler]] = ()):
        self._handlers: dict[str, ConfigHandler] = {}
        self._register_handlers(handlers)
    def add_handler(self, handler: Type[ConfigHandler]):
        for extension in handler.extensions:
            self._handlers[extension.casefold()] = handler()

    def remove_handler(self, handler: Type[ConfigHandler]):
        for extension in handler.extensions:
            del self._handlers[extension.casefold()]

    def _register_handlers(self, handlers: Sequence[Type[ConfigHandler]]):
        for handler in handlers:
            self.add_handler(handler)
