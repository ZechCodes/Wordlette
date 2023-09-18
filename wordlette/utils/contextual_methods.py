from types import MethodType
from typing import Callable, ParamSpec, TypeVar, Self

P = ParamSpec("P")
R = TypeVar("R")


class ContextualMethod:
    def __init__(self, method: Callable[P, R]):
        self._method = method
        self._classmethod = method

    def classmethod(self, method: Callable[P, R]) -> Self:
        if method.__name__ != self._method.__name__:
            raise ValueError(
                f"Method name {method.__name__!r} does not match {self._method.__name__!r}"
            )

        self._classmethod = method
        return self

    def __get__(self, instance, owner) -> Callable[P, R]:
        if instance is None:
            return MethodType(self._classmethod, owner)

        return MethodType(self._method, instance)


def contextual_method(func: Callable[P, R]) -> ContextualMethod:
    return ContextualMethod(func)
