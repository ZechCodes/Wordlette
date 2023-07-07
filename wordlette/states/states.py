from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from wordlette.options import Option
from wordlette.states.machine import StateMachine

T = TypeVar("T")


class State(Generic[T], ABC):
    def __init__(self):
        self._value: Option[T] = Option.Null()

    @property
    def value(self) -> T | None:
        match self._value:
            case Option.Value(value):
                return value

            case Option.Null():
                self.value = value = self._default_factory()
                return value

    @value.setter
    def value(self, new_value: T | Option[T]):
        match new_value:
            case Option() as value:
                self._value = value

            case value:
                self._value = Option.Value(value)

    @property
    def optional_value(self) -> Option[T]:
        return self._value

    @abstractmethod
    async def enter_state(self):
        ...

    async def exit_state(self):
        return

    async def next_state(self) -> "Option[Type[State]]":
        return Option.Null()

    @classmethod
    async def start(cls) -> StateMachine[T]:
        machine = StateMachine(cls)
        await machine.start()
        return machine

    def _default_factory(self) -> T | None:
        return None


class NullState(State):
    async def enter_state(self):
        ...

    async def next_state(self) -> "Option[Type[State]]":
        return Option.Null()
