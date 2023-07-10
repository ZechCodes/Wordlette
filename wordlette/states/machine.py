from asyncio import Queue
from typing import Coroutine, Generic, Type, TypeVar

from wordlette.options import Option
from wordlette.states import State
from wordlette.states.states import InitialState, RequestCycle

T = TypeVar("T")


class StateMachine(Generic[T]):
    def __new__(cls, *states):
        machine = super().__new__(cls)
        machine.__init__(*states)
        machine.__state_machine = machine

        view = object.__new__(StateMachineView)
        view.__dict__ = machine.__dict__
        return view

    def __init__(self, *states: Type[State]):
    def __init__(self, *states: Type[State[T]]):
        self._states = states
        self._current_state = InitialState(states[0])
        self._value = None
        self._stopped = True

        self._transition_stack = Queue()

    @property
    def state(self) -> State[T]:
        return self._current_state

    @property
    def stopped(self) -> bool:
        return self._stopped

    @property
    def value(self) -> T:
        return self._value

    def cycle(self) -> Coroutine[None, None, None]:
        return self._queue_next_state()

    async def _queue_next_state(self):
        match await self._current_state.get_next_state():
            case Option.Null():
                self._stopped = True
                self._current_state = None

            case Option.Value(constructor) | constructor:
                await self._transition_stack.put(constructor())

    async def _enter_state(self):
        match await self._current_state.enter_state():
            case RequestCycle(value):
                await self._queue_next_state()

            case value:
                ...

        match value:
            case Option.Null() | None:
                return

            case Option.Value(value) | value:
                self._value = value

    def _exit_state(self) -> Coroutine[None, None, None]:
        return self._current_state.exit_state()


class StateMachineView(StateMachine[T]):
    async def cycle(self):
        await self._queue_next_state()
        self._stopped = False
        while not self._transition_stack.empty():
            await self._exit_state()
            self._current_state = await self._transition_stack.get()
            await self._enter_state()
