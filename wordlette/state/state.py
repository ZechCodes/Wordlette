from __future__ import annotations
from typing import Any, Awaitable, Callable, ParamSpec, TypeAlias
from inspect import iscoroutinefunction
from wordlette.exceptions import (
    WordletteTransitionFailed,
    WordletteTransitionImpossible,
)
from wordlette.smart_functions import call
from functools import partial


P = ParamSpec("P")
Transition: TypeAlias = Callable[[P], Awaitable | None]


class State:
    def __init__(self, name: str, enter_transition: Transition | None = None):
        self._name = name
        self._transitions: dict[State, Transition] = {}
        self._enter = enter_transition

    @property
    def deadend(self) -> bool:
        return len(self._transitions) == 0

    @property
    def name(self) -> str:
        return self._name

    def add_transition(self, state: State, transition: Transition):
        """Adds a transition from this state to a different state."""
        self._transitions[state] = self._wrap_transition(transition, self, state)

    async def enter(self, from_state: State):
        if not self._enter:
            return

        enter_transition = self._wrap_transition(self._enter, from_state, self)
        await enter_transition()

    def remove_transition(self, state: State):
        """Removes a transition from this state to a different state."""
        del self._transitions[state]

    async def transition(self, state: State):
        """Runs the transition function that goes from this state to the requested state.

        Raises WordletteTransitionImpossible if there is no transition registered for the requested state.
        Raises WordletteTransitionFailed if an exception when the transition function is called."""
        transition = self._get_transition(state)
        await self._run_transition(transition, state)
        await state.enter(self)

    def _get_transition(self, state: State) -> Transition:
        try:
            return self._transitions[state]
        except KeyError as exception:
            raise WordletteTransitionImpossible(
                f"{self} has no transitions that go to {state}"
            ) from exception

    async def _run_transition(self, transition: Transition, state: State):
        try:
            await transition()
        except Exception as exception:
            raise WordletteTransitionFailed(
                f"The transition from {self} to {state} failed with an {type(exception).__name__} exception."
            )

    def _wrap_transition(
        self, transition: Transition, from_state: State, to_state: State
    ) -> Callable[P, Awaitable[None]]:
        if iscoroutinefunction(transition):
            return partial(call, transition, from_state=from_state, to_state=to_state)

        async def async_wrapper(*args, **kwargs):
            kwargs.setdefault("from_state", from_state)
            kwargs.setdefault("to_state", to_state)
            call(transition, *args, **kwargs)

        return async_wrapper

    def __repr__(self):
        args = [f"{self.name!r}"]
        args.extend(
            f"{name}={transition.__name__ if hasattr(transition, '__name__') else '???'}(...)"
            for name, transition in self._transitions.items()
        )
        return f"{type(self).__name__}({', '.join(args)})"
