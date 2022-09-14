from typing import Awaitable, Callable, TypeVar, ParamSpec, TypeAlias

R = TypeVar("R")
P = ParamSpec("P")

Listener: TypeAlias = Callable[P, Awaitable[R]]


class ClassOrInstanceDispatch:
    def __init__(self, method: Callable[P, R]):
        self._class_method = None
        self._instance_method = None

        self.add_method(method)

    def __get__(self, instance, owner) -> Callable[P, R]:
        method = self._class_method
        if instance:
            method = self._instance_method

        return method.__get__(instance, owner)

    def add_method(self, method: Callable[P, R]):
        match method:
            case classmethod():
                self._class_method = method
            case _:
                self._instance_method = method

        return self
