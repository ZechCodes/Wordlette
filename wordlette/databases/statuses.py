from abc import ABC
from typing import TypeVar

from wordlette.utils.options import Value, Null, Option

T = TypeVar("T")


class DatabaseStatus(Option[T], ABC):
    pass


class DatabaseExceptionStatus(DatabaseStatus, Null):
    def __eq__(self, other):
        if not isinstance(other, DatabaseStatus):
            raise NotImplementedError()

        if not isinstance(other, DatabaseExceptionStatus):
            return False

        return self.exception == self.exception


class DatabaseSuccessStatus(DatabaseStatus, Value):
    def __eq__(self, other):
        if not isinstance(other, DatabaseStatus):
            return NotImplemented

        if not isinstance(other, DatabaseSuccessStatus):
            return False

        return self.value == other.value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"
