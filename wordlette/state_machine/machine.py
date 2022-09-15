from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Type, TypeVar

from wordlette.events import Eventable
from wordlette.exceptions import WordletteStateMachineAlreadyStarted
from .state import State

S = TypeVar("S", bound=State)


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


class StateMachine(Generic[S], Eventable):
    def __init__(self):
        super().__init__()
        self._current_state: S | None = None
        self._transition_depth = DepthCounter()

    @property
    def started(self) -> bool:
        return self._current_state is not None

    @property
    def state(self) -> S:
        return self._current_state

    async def start(self, initial_state_type: Type[S]):
        if self.started:
            raise WordletteStateMachineAlreadyStarted(
                f"The state machine ({self}) has already been started"
            )

        await self._transition_to_state(initial_state_type)

    async def next(self):
        next_state_type = await self._current_state.next()
        await self._transition_to_state(next_state_type)

    async def _transition_to_state(self, state_type: Type[S]):
        old_state, self._current_state = self._current_state, self.bevy.create(
            state_type
        )
        async with self._transition_depth:
            transition_immediately = await self._current_state.enter()
            await self._dispatch(
                "transitioned-to-state", old_state, self._current_state
            )

            if transition_immediately:
                await self.next()

        if self._transition_depth.count == 0:
            await self._dispatch("entered-state", old_state, self._current_state)

    def __repr__(self):
        return f"{type(self).__name__}(state={self.state})"

    async def _dispatch(self, event: str, old_state: State, new_state: State):
        payload = StateChangeEvent(event, old_state, new_state)
        await self.dispatch(event, payload)
        await self.dispatch(f"{event}[{new_state.name}]", payload)
