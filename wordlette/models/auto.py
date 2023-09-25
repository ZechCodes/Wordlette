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


class Auto(Generic[P, R]):
    def __init__(self, func: Callable[P, R] | None):
        self.func = func

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    def __ror__(self, other: Any) -> UnionType:
        return Union[other, self]

    def __repr__(self) -> str:
        return f"<Auto: {self.func}>"
