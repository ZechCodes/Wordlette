from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import Generic, Type, TypeVar

from wordlette import Logging
from wordlette.events import Eventable
from wordlette.exceptions import WordletteStateMachineAlreadyStarted
from wordlette.utilities.depth_counter import DepthCounter
from .null_state import NullState
from .state import State


S = TypeVar("S", bound=State)


class StateEnterContext:
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self.transition_to: Type[State] | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(
        self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType
    ):
        if not exc_type:
            return False

        exc_val.state = self.state_machine.state
        self.state_machine.last_exception = exc_val
        self.transition_to = await self.state_machine.state.on_error_next_state(exc_val)
        return bool(self.transition_to)


@dataclass()
class StateChangeEvent:
    old_state: State
    new_state: State
    event: str


class StateMachine(Generic[S], Eventable):
    def __init__(self):
        super().__init__()
        self._transition_depth = DepthCounter()
        self._current_state: S = NullState()
        self.last_exception = None

    @property
    def started(self) -> bool:
        return not isinstance(self._current_state, NullState)

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
        next_state_type = await self._current_state.next_state()
        await self._transition_to_state(next_state_type)

    async def _transition_to_state(self, state_type: Type[S]):
        old_state, self._current_state = self._current_state, self._create_state(
            state_type
        )
        async with self._transition_depth:
            async with StateEnterContext(self) as enter_context:
                transition_immediately = await self._current_state.enter_state()

            await self._dispatch(
                old_state, self._current_state, event="transitioned-to-state"
            )

            if enter_context.transition_to:
                await self._transition_to_state(enter_context.transition_to)

            elif transition_immediately:
                await self.next()

        if self._transition_depth.count == 0:
            await self._dispatch(old_state, self._current_state, event="entered-state")

    def __repr__(self):
        return f"{type(self).__name__}(state={self.state})"

    def _create_state(self, state_type: Type[State]) -> State:
        logger = self.bevy.create(Logging[state_type.__name__], cache=False)
        context = self.bevy.branch()
        context.add(logger, use_as=Logging)
        return context.create(state_type)

    async def _dispatch(self, old_state: State, new_state: State, **labels):
        payload = StateChangeEvent(old_state, new_state, **labels)
        await self.dispatch(payload, **labels, state=new_state.name)
