from asyncio import Queue
from typing import Coroutine, Generic, Type, TypeAlias, TypeVar

import wordlette.states
from wordlette.options import Option

T = TypeVar("T")
State: TypeAlias = "wordlette.states.State[T]"


class StateMachine(Generic[T]):
    def __init__(self, state: Type[State]):
        self._initial_state = state
        self._state = wordlette.states.states.NullState()
        self._transitions = Queue()

    @property
    def value(self) -> T:
        return self._state.value

    @property
    def state(self) -> State:
        return self._state

    async def start(self):
        await self._transitions.put(self._initial_state())
        await self._clear_transitions()

    async def _clear_transitions(self):
        while not self._transitions.empty():
            state = await self._transitions.get()
            await self._exit_current_state()
            transition = await self._enter_new_state(state)
            self._state = state

            if transition:
                await self._transitions.put(await self._get_next_state())

    async def _get_next_state(self) -> State:
        match await self._state.next_state():
            case Option.Value(constructor):
                state = constructor()

            case Option.Null() | _:
                state = wordlette.states.states.NullState()

        return state

    async def _enter_new_state(self, state: State) -> bool:
        return await state.enter_state()

    def _exit_current_state(self) -> Coroutine[None, None, None]:
        return self._state.exit_state()

    async def next(self) -> State:
        await self._transitions.put(await self._get_next_state())
        await self._clear_transitions()
        return self._state
