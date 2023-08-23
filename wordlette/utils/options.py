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
        self._exception = exception

    @property
    def exception(self) -> BaseWordletteException:
        return self._exception or self._create_exception()

    def exception_or(self, _) -> BaseWordletteException:
        return self.exception

    @property
    def value(self) -> NoReturn:
        raise self._create_exception()

    def value_or(self, default: T) -> T:
        return default

    def __bool__(self):
        return False

    def _create_exception(self) -> NoValueException:
        exception = NoValueException("Null options have no value")
        if self._exception:
            exc_type = type(self._exception)
            exception.add_note(
                f"└─── caused by {exc_type.__module__}.{exc_type.__qualname__}: {self._exception}"
            )

        return exception


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
