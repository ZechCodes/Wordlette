from typing import Type

import pytest

from wordlette.options import Option
from wordlette.states import State


@pytest.mark.asyncio
async def test_statemachine():
    entered_a = False
    entered_b = False

    class StateA(State):
        async def enter_state(self):
            nonlocal entered_a
            entered_a = True

        async def next_state(self) -> "Option[Type[StateB]]":
            return Option.Value(StateB)

    class StateB(State):
        async def enter_state(self):
            nonlocal entered_b
            entered_b = True

    machine = await StateA.start()
    await machine.next()
    assert entered_a
    assert entered_b


@pytest.mark.asyncio
async def test_state_value():
    class StateA(State[int]):
        async def enter_state(self):
            self.value = 1

        async def next_state(self) -> "Option[Type[StateB]]":
            return Option.Value(StateB)

    class StateB(State[int]):
        async def enter_state(self):
            self.value = 2

    machine = await StateA.start()
    await machine.next()
    assert machine.value == 2


@pytest.mark.asyncio
async def test_immediate_transition():
    class StateA(State[int]):
        async def enter_state(self):
            return True

        async def next_state(self) -> "Option[Type[StateB]]":
            return Option.Value(StateB)

    class StateB(State[int]):
        async def enter_state(self):
            return

    machine = await StateA.start()
    assert isinstance(machine.state, StateB)
