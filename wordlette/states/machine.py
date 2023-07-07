from typing import Coroutine, Generic, Type, TypeAlias, TypeVar

import wordlette.states
from wordlette.options import Option

T = TypeVar("T")
State: TypeAlias = "wordlette.states.State[T]"


class StateMachine(Generic[T]):
    def __init__(self, state: Type[State]):
        self._initial_state = state
        self._state = wordlette.states.states.NullState()

    @property
    def value(self) -> T:
        return self._state.value

    @property
    def state(self) -> State:
        return self._state

    async def start(self):
        self._state = self._initial_state()
        await self._state.enter_state()

    async def _enter_next_state(self) -> State:
        match await self._state.next_state():
            case Option.Value(constructor):
                state = constructor()

            case Option.Null() | _:
                state = wordlette.states.states.NullState()

        await state.enter_state()
        return state

    def _exit_current_state(self) -> Coroutine[None, None, None]:
        return self._state.exit_state()

    async def next(self) -> State:
        await self._exit_current_state()
        self._state = await self._enter_next_state()
        return self._state
