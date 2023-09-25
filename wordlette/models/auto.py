from types import UnionType
from typing import (
    Callable,
    ParamSpec,
    TypeVar,
    Generic,
    Any,
    Union,
)

P = ParamSpec("P")
R = TypeVar("R")


class AutoSet(Generic[P, R]):
    def __init__(self, func: Callable[P, R]):
        self.func = func

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    def __ror__(self, other: Any) -> UnionType:
        return Union[other, self]

    def __repr__(self) -> str:
        return f"<AutoSet: {self.func}>"


class Auto:
    def __class_getitem__(cls, func: Callable[P, R]) -> AutoSet[P, R]:
        return AutoSet(func)
