from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

T = TypeVar("T")


class NoValueException(Exception):
    pass


class Option(Generic[T], ABC):
    Value: "Type[Value[T]]"
    Null: "Type[Null[T]]"

    @property
    @abstractmethod
    def value(self) -> T:
        ...

    @abstractmethod
    def value_or(self, default: T) -> T:
        ...

    @abstractmethod
    def __bool__(self):
        ...


class Null(Option[T]):
    @property
    def value(self) -> T:
        raise NoValueException("Null options have no value")

    def value_or(self, default: T) -> T:
        return default

    def __bool__(self):
        return False


class Value(Option[T]):
    __match_args__ = ("value",)

    def __init__(self, value: T):
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def value_or(self, default: T) -> T:
        return self._value

    def __bool__(self):
        return True


Option.Value = Value
Option.Null = Null
