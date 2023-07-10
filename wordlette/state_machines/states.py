from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar, Coroutine

from wordlette.options import Option
from wordlette.state_machines.predicates import always

T = TypeVar("T")


class RequestCycle:
    pass


class State(Generic[T], ABC):
    transitions = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.transitions = cls.transitions.copy()

    def cycle(self) -> RequestCycle:
        return RequestCycle()

    @abstractmethod
    async def enter_state(self) -> RequestCycle | None:
        ...

    async def exit_state(self):
        return

    async def get_next_state(self) -> "Option[Type[State]]":
        for state, predicate in self.transitions.items():
            if await predicate():
                return Option.Value(state)

        return Option.Null()

    @classmethod
    def goes_to(cls, state: "Type[State]", when: Coroutine[None, None, bool] = always):
        state_cls = cls
        if not cls.transitions:
            state_cls = type(cls.__name__, (cls,), {})

        state_cls.transitions[state] = when
        return state_cls


class NullState(State[T]):
    async def enter_state(self) -> None:
        return None

    async def get_next_state(self) -> "Option[Type[State[T]]]":
        return Option.Null()


class InitialState(NullState[T]):
    def __init__(self, state: Type[State[T]]):
        super().__init__()
        self._state = state

    async def get_next_state(self) -> "Option[Type[State[T]]]":
        return Option.Value(self._state)
