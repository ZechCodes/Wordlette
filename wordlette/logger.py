from logging import Logger

from typing import Type

from bevy.providers import TypeProvider


class Logging(Logger):
    def __init__(self, name: str):
        self.name = name

    def __class_getitem__(cls, name):
        return cls(name)


class LoggingProvider(TypeProvider, priority="high"):
    def bind_to_context(
        self, obj: Logging | Type[Logging], context
    ) -> Logging | Type[Logging]:
        return obj

    def create(self, obj: Logging | Type[Logging], add: bool = False) -> Logger:
        if obj not in self._repository and isinstance(obj, Logging):
            parent_logger: Logger = self.get(Logging)
            logger = parent_logger.getChild(f"{obj.name}")
            logger.addHandler(parent_logger.handlers[0])
            self._repository[obj] = logger

        return self.get(obj)

    def get(
        self, obj: Logging | Type[Logging], default: Logger | None = None
    ) -> Logger:
        if obj in self._repository:
            return self._repository[obj]

        if isinstance(obj, Logging):
            return self.create(obj)

        return super().get(obj, default)

    def supports(self, obj) -> bool:
        if isinstance(obj, Logging):
            return True

        return isinstance(obj, type) and issubclass(obj, Logging)
