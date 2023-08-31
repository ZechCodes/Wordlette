import logging
from abc import ABCMeta, abstractmethod
from typing import Generic, Type, TypeVar, ParamSpec, Callable, Awaitable

from wordlette.state_machines.predicates import always

logger = logging.getLogger("StateMachine")

_T = TypeVar("_T")
_P = ParamSpec("_P")


class RequestCycle:
    pass


class Transition:
    __match_args__ = ("state", "to_state", "predicate")

    def __init__(
        self,
        state: "Type[State[_T]]",
        to_state: "Type[State[_T]]",
        predicate: Callable[[], Awaitable[bool]],
    ):
        self.state = state
        self.to_state = to_state
        self.predicate = predicate


class StateABCMeta(ABCMeta):
    def __repr__(cls):
        return f"<class State:{cls.__name__}>"


class State(Generic[_T], metaclass=StateABCMeta):
    transitions = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.transitions = cls.transitions.copy()

    def cycle(self) -> RequestCycle:
        return RequestCycle()

    @abstractmethod
    async def enter_state(self, *_, **__) -> RequestCycle | None:
        ...

    async def exit_state(self, *_, **__) -> None:
        return

    def __repr__(self):
        return f"<State:{self.__class__.__name__}>"

    @classmethod
    def goes_to(
        cls, state: "Type[State[_T]]", when: Callable[_P, Awaitable[bool]] = always
    ) -> Transition:
        return Transition(cls, state, when)


class NullState(State[_T]):
    async def enter_state(self) -> None:
        return None


class InitialState(NullState[_T]):
    pass
