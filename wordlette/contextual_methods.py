from types import MethodType
from typing import Callable, ParamSpec, TypeVar, Self

P = ParamSpec("P")
R = TypeVar("R")


class ContextualMethod:
    def __init__(self, method: Callable[P, R]):
        self.method = method
        self.class_method = method

    def classmethod(self, method: Callable[P, R]) -> Self:
        if method.__name__ != self.method.__name__:
            raise ValueError(
                f"Method name {method.__name__!r} does not match {self.method.__name__!r}"
            )

        self.class_method = method
        return self

    def __get__(self, instance, owner) -> Callable[P, R]:
        if instance is None:
            return MethodType(self.class_method, owner)

        return MethodType(self.method, instance)


def contextual_method(func: Callable[P, R]) -> ContextualMethod:
    return ContextualMethod(func)
