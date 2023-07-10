from abc import ABC, abstractmethod
import logging
from typing import Generic, Type, TypeVar, ParamSpec, Callable, Awaitable

from wordlette.options import Option
from wordlette.state_machines.predicates import always

logger = logging.getLogger("StateMachine")

_T = TypeVar("_T")
_P = ParamSpec("_P")


class RequestCycle:
    pass


class StateABCMeta(ABCMeta):
    def __repr__(cls):
        transitions = (
            ", ".join(sorted(repr(transition) for transition in cls.transitions))
            if cls.transitions
            else ""
        )
        return f"<Class:State:{cls.__name__} [{transitions}]>"


class State(Generic[_T], metaclass=StateABCMeta):
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

    async def get_next_state(self) -> "Option[Type[State[_T]]]":
        for state, predicate in self.transitions.items():
            logger.debug(f"Checking {state} with {predicate}")
            if await predicate():
                return Option.Value(state)

        return Option.Null()

    @classmethod
    def goes_to(
        cls, state: "Type[State[_T]]", when: Callable[_P, Awaitable[bool]] = always
    ):
        state_cls = cls
        if not cls.transitions:
            logger.debug(f"CREATING TRANSITION DICT FOR {cls} {id(cls)}")
            state_cls = type(cls.__name__, (cls,), {})

        state_cls.transitions[state] = when
        return state_cls


class NullState(State[_T]):
    async def enter_state(self) -> None:
        return None

    async def get_next_state(self) -> "Option[Type[State[_T]]]":
        return Option.Null()


class InitialState(NullState[_T]):
    def __init__(self, state: Type[State[_T]]):
        super().__init__()
        self._state = state

    async def get_next_state(self) -> "Option[Type[State[_T]]]":
        return Option.Value(self._state)
