from __future__ import annotations
from wordlette.state_machine.state import State
from wordlette.exceptions import WordletteStateMachineAlreadyStarted
from typing import Generic, ParamSpec, TypeVar


P = ParamSpec("P")
T = TypeVar("T")


class StateMachine(Generic[T, P]):
    def __init__(self):
        self._current_state: State[T, P] | None = None
        self._current_value: T | None = None

    @property
    def state(self) -> State[T, P]:
        return self._current_state

    @property
    def value(self) -> T:
        return self._current_value

    async def start(
        self, initial_state: State[T, P], *args: P.args, **kwargs: P.kwargs
    ) -> StateMachine[T, P]:
        if self._current_state:
            raise WordletteStateMachineAlreadyStarted(
                f"{self} has already been started"
            )

        await self._set_current_state(initial_state, *args, **kwargs)
        return self

    async def next(self, *args: P.args, **kwargs: P.kwargs) -> T:
        next_state = await self._current_state.next(self, *args, **kwargs)
        return await self._set_current_state(next_state, *args, **kwargs)

    async def _set_current_state(
        self, new_state: State[T, P], *args: P.args, **kwargs: P.kwargs
    ) -> T:
        if self._current_state:
            await self._current_state.leave(self, *args, **kwargs)

        self._current_state = new_state
        self._current_value = await self._current_state.run(self, *args, **kwargs)
        return self._current_value
