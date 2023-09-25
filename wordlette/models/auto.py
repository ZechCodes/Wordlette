from types import UnionType
from typing import (
    ParamSpec,
    TypeVar,
    Generic,
    Any,
    Union,
)

P = ParamSpec("P")
R = TypeVar("R")


class Auto(Generic[P, R]):
    def __ror__(self, other: Any) -> UnionType:
        return Union[other, self]

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"
