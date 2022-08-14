from __future__ import annotations
from typing import Awaitable, Callable, Generic, ParamSpec, TypeAlias, TypeVar
from wordlette.exceptions import WordletteNoTransitionFound


P = ParamSpec("P")
T = TypeVar("T")

Predicate: TypeAlias = Callable[[P], Awaitable[bool]]
StateRunFunction: TypeAlias = Callable[[P], Awaitable[T]]
StateLeaveFunction: TypeAlias = Callable[[P], Awaitable[None]]


class State(Generic[T, P]):
    def __init__(self, run: StateRunFunction):
        self._run = run
        self._leave: StateLeaveFunction | None = None
        self.transitions: dict[State[T, P], Transition] = {}
        self.name = None

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"

    def __rshift__(self, to_state: State) -> Callable[[Predicate], Transition]:
        def get_predicate(predicate: Predicate) -> Transition:
            self.transitions[to_state] = Transition(self, to_state, predicate)
            return self.transitions[to_state]

        return get_predicate

    def __set_name__(self, owner, name):
        self.name = name

    async def leave(self, *args: P.args, **kwargs: P.args):
        if self._leave:
            await self._leave(*args, **kwargs)

    async def next(self, *args: P.args, **kwargs: P.kwargs) -> State[T, P]:
        for state, transition in self.transitions.items():
            if await transition.can_transition(*args, **kwargs):
                return state
        else:
            raise WordletteNoTransitionFound(
                f"{self} has no transitions that match the given arguments\n  {args=}\n  {kwargs=}"
            )

    def on_leave(self, leave: StateLeaveFunction) -> State[T, P]:
        self._leave = leave
        return self

    async def run(self, *args: P.args, **kwargs: P.args) -> T:
        return await self._run(*args, **kwargs)


class Transition:
    def __init__(self, from_state: State, to_state: State, predicate: Predicate):
        self.from_state = from_state
        self.to_state = to_state
        self.predicate = predicate
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    async def can_transition(self, *args: P.args, **kwargs: P.kwargs) -> bool:
        return await self.predicate(*args, **kwargs)
