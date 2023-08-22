import logging
from asyncio import Queue
from collections import defaultdict
from typing import Coroutine, Generic, Type, TypeVar

from wordlette.events import Observable
from wordlette.state_machines.predicates import always
from wordlette.state_machines.states import (
    State,
    InitialState,
    RequestCycle,
    Transition,
)
from wordlette.utils.maybe_awaitables import maybe_awaitable
from wordlette.utils.options import Option

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("StateMachine")

T = TypeVar("T")


class StoppedState(State[T]):
    async def enter_state(self):
        return


class StateMachine(Generic[T], Observable):
    def __init__(self, *states: Type[State] | Transition):
        self._states = self._build_state_graph(
            self._create_initial_state_transition(states[0]), *states
        )
        self._current_state = InitialState()
        self._stopped = True

        self._transition_stack = Queue()

    @property
    def state(self) -> State[T]:
        return self._current_state

    @property
    def started(self) -> bool:
        return not isinstance(self._current_state, InitialState)

    @property
    def stopped(self) -> bool:
        return self._stopped

    async def cycle(self):
        await self._queue_next_state()
        self._stopped = False
        while not self._transition_stack.empty():
            await self._exit_state()
            self._current_state = await self._transition_stack.get()
            logger.debug(f"Transitioning to {self._current_state}")
            await self._enter_state()

    async def _queue_next_state(self):
        match await self._get_next_state():
            case Option.Null():
                self._stopped = True
                await self._transition_stack.put(StoppedState())

            case Option.Value(constructor):
                await self._transition_stack.put(self._construct_state(constructor))

    async def _enter_state(self):
        match await maybe_awaitable(self._current_state.enter_state()):
            case RequestCycle():
                await self._queue_next_state()

    def _construct_state(self, constructor: Type[State[T]]) -> State[T]:
        state = constructor()
        if isinstance(state, Observable):
            state.__event_dispatch__.propagate_to(self.emit)

        return state

    def _exit_state(self) -> Coroutine[None, None, None]:
        return self._current_state.exit_state()

    def _build_state_graph(
        self, *states: Type[State] | Transition
    ) -> dict[Type[State[T]], dict]:
        graph = defaultdict(dict)
        for transition in states:
            match transition:
                case Transition(state, to_state, predicate):
                    graph[state][to_state] = predicate

                case type() as state if issubclass(state, State):
                    graph[state][StoppedState] = always

        return graph

    async def _get_next_state(self) -> Option[Type[State[T]]]:
        logger.debug(f"Finding next state from {self._current_state}")
        for next_state, predicate in self._states[type(self._current_state)].items():
            logger.debug(
                f"....Checking {next_state} when <{type(predicate).__name__}:{predicate.__name__}>"
            )
            if await predicate():
                return Option.Value(next_state)

        return Option.Null()

    def _create_initial_state_transition(
        self, state: Type[State[T]] | Transition
    ) -> Transition:
        match state:
            case Transition(state, _, _):
                return Transition(InitialState, state, always)

            case type() as state if issubclass(state, State):
                return Transition(InitialState, state, always)
