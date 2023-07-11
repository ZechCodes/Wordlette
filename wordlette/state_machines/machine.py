import logging
from asyncio import Queue
from typing import Coroutine, Generic, Type, TypeVar, Sequence

from wordlette.state_machines.predicates import always
from wordlette.state_machines.states import (
    State,
    InitialState,
    RequestCycle,
    Transition,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("StateMachine")

T = TypeVar("T")


class StoppedState(State[T]):
    async def enter_state(self):
        return


class StateMachine(Generic[T]):
    def __init__(self, *states: Transition):
        self._states = self._build_state_graph(
            (Transition(InitialState, states[0].state, always), *states)
        )
        self._current_state = InitialState()
        self._stopped = True

        self._transition_stack = Queue()

    @property
    def state(self) -> State[T]:
        return self._current_state

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
            case None:
                self._stopped = True
                self._current_state = StoppedState()

            case constructor:
                await self._transition_stack.put(constructor())

    async def _enter_state(self):
        match await self._current_state.enter_state():
            case RequestCycle():
                await self._queue_next_state()

    def _exit_state(self) -> Coroutine[None, None, None]:
        return self._current_state.exit_state()

    def _build_state_graph(
        self, states: Sequence[Transition]
    ) -> dict[Type[State[T]], dict]:
        graph = {}
        for transition in states:
            graph.setdefault(transition.state, {})
            graph[transition.state][transition.to_state] = transition.predicate

        return graph

    async def _get_next_state(self) -> Type[State[T]] | None:
        logger.debug(f"Finding next state from {self._current_state}")
        for next_state, predicate in self._states[type(self._current_state)].items():
            logger.debug(
                f"....Checking {next_state} when <{type(predicate).__name__}:{predicate.__name__}>"
            )
            if await predicate():
                return next_state

        return
