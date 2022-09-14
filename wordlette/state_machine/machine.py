from __future__ import annotations

import asyncio
from bevy import Context
from dataclasses import dataclass
from typing import Any, Generic, ParamSpec, TypeVar

from wordlette.events import Eventable
from wordlette.exceptions import WordletteStateMachineAlreadyStarted
from wordlette.state_machine.state import State

P = ParamSpec("P")
T = TypeVar("T")


class TransitionResultFuture(asyncio.Task):
    ...


class DepthCounter:
    def __init__(self):
        self.count = 0

    async def __aenter__(self):
        self.count += 1

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.count -= 1


@dataclass()
class StateChangeEvent:
    event: str
    old_state: State
    new_state: State
    context: Context
    args: tuple[Any]
    kwargs: dict[str, Any]


class StateMachine(Generic[T, P], Eventable):
    def __init__(self):
        super().__init__()
        self._current_state: State[T, P] | None = None
        self._current_value: T | None = None
        self._entered_states = DepthCounter()

    @State
    async def starting(self):
        ...

    @property
    def started(self) -> bool:
        return self._current_state is not None

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
        old_state = self.state
        await self._dispatch("changing-state", old_state, new_state, args, kwargs)
        if self._current_state:
            await self._current_state.leave(self, *args, **kwargs)

        self._current_state = new_state
        async with self._entered_states:
            self._current_value = await self._current_state.run(self, *args, **kwargs)

        if self._entered_states.count == 0:
            await self._dispatch("changed-state", old_state, self.state, args, kwargs)

        return self._current_value

    def __repr__(self):
        return f"{type(self).__name__}(state={self.state})"

    async def _dispatch(
        self,
        event: str,
        old_state: State,
        new_state: State,
        args: tuple[Any],
        kwargs: dict[str, Any],
    ):
        payload = StateChangeEvent(
            event, old_state, new_state, self.value, args, kwargs
        )
        await self.dispatch(event, payload)
        await self.dispatch(f"{event}[{new_state.name}]", payload)
