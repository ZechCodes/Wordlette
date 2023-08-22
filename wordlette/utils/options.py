from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar, NoReturn

from wordlette.core.exceptions import BaseWordletteException

E = TypeVar("E")
T = TypeVar("T")


class NoValueException(BaseWordletteException):
    pass


class Option(Generic[T], ABC):
    Value: "Type[Value[T]]"
    Null: "Type[Null[T]]"

    @property
    @abstractmethod
    def exception(self) -> BaseWordletteException | NoReturn:
        ...

    @abstractmethod
    def exception_or(self, default: E) -> BaseWordletteException | E:
        ...

    @property
    @abstractmethod
    def value(self) -> T | NoReturn:
        ...

    @abstractmethod
    def value_or(self, default: T) -> T:
        ...

    @abstractmethod
    def __bool__(self):
        ...


class Null(Option[T]):
    __match_args__ = ("exception",)

    def __init__(self, exception: BaseWordletteException | None = None):
        self._exception = NoValueException("Null options have no value")
        if exception is not None:
            self._exception.__cause__ = exception

    @property
    def exception(self) -> BaseWordletteException:
        return self._exception

    def exception_or(self, _) -> BaseWordletteException:
        return self._exception

    @property
    def value(self) -> NoReturn:
        raise self._exception

    def value_or(self, default: T) -> T:
        return default

    def __bool__(self):
        return False


class Value(Option[T]):
    __match_args__ = ("value",)

    def __init__(self, value: T):
        self._value = value

    @property
    def exception(self) -> NoReturn:
        raise NoValueException("Value options have no exception")

    def exception_or(self, default: E) -> E:
        return default

    @property
    def value(self) -> T:
        return self._value

    def value_or(self, default: T) -> T:
        return self._value

    def __bool__(self):
        return True


Option.Value = Value
Option.Null = Null
