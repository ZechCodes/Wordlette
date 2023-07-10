from asyncio import Queue
from typing import Coroutine, Generic, Type, TypeVar

from wordlette.options import Option
from wordlette.state_machines.states import State, InitialState, RequestCycle

T = TypeVar("T")


class StoppedState(State[T]):
    async def enter_state(self):
        return


class StateMachine(Generic[T]):
    def __init__(self, *states: Type[State[T]]):
        self._states = states
        self._current_state = InitialState(states[0])
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
            await self._enter_state()

    async def _queue_next_state(self):
        match await self._current_state.get_next_state():
            case Option.Null():
                self._stopped = True
                self._current_state = StoppedState()

            case Option.Value(constructor) | constructor:
                await self._transition_stack.put(constructor())

    async def _enter_state(self):
        match await self._current_state.enter_state():
            case RequestCycle():
                await self._queue_next_state()

    def _exit_state(self) -> Coroutine[None, None, None]:
        return self._current_state.exit_state()
