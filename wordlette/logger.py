from logging import Logger

import logging
import sys
import uvicorn.logging
from functools import cache
from typing import Type

from bevy.providers import TypeProvider


class Logging(Logger):
    name = "wordlette"

    def __init__(self, name: str):
        self.name = name

    def __class_getitem__(cls, name):
        return cls(name)


class LoggingProvider(TypeProvider, priority="high"):
    def bind_to_context(
        self, obj: Logging | Type[Logging], context
    ) -> Logging | Type[Logging]:
        return obj

    def create(
        self, obj: Logging | Type[Logging], name: str = "", add: bool = False, **_
    ) -> Logger | None:
        if isinstance(obj, Logging):
            logger = self._create_child_logger(obj)

        elif issubclass(obj, Logging):
            logger = _create_logger(name or obj.name)

        else:
            return None

        if add:
            self._repository[obj] = logger

        return logger

    def _create_child_logger(self, obj):
        parent_logger: Logger = self.bevy.get(Logging)
        logger = parent_logger.getChild(f"{obj.name}")
        return logger

    def get(
        self, obj: Logging | Type[Logging], default: Logger | None = None
    ) -> Logger:
        if obj in self._repository:
            return self._repository[obj]

        if isinstance(obj, Logging):
            return self.create(obj, add=True)

        return self.create(obj, add=True)

    def supports(self, obj) -> bool:
        if isinstance(obj, Logging):
            return True

        return isinstance(obj, type) and issubclass(obj, Logging)


@cache
def _create_logger(name):
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = uvicorn.logging.DefaultFormatter(
        "%(levelprefix)s %(asctime)s %(name)s  ::  %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setStream(sys.stdout)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
