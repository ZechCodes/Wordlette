import pytest

from wordlette.states import State
from wordlette.states.machine import StateMachine


@pytest.mark.asyncio
async def test_statemachine():
    entered_a = False
    entered_b = False

    class StateA(State):
        async def enter_state(self):
            nonlocal entered_a
            entered_a = True
            return self.cycle()

    class StateB(State):
        async def enter_state(self):
            nonlocal entered_b
            entered_b = True

    machine = StateMachine(StateA.goes_to(StateB))

    await machine.cycle()
    assert entered_a
    assert entered_b


@pytest.mark.asyncio
async def test_state_value():
    class StateA(State[int]):
        async def enter_state(self):
            return 1 & self.cycle()

    class StateB(State[int]):
        async def enter_state(self):
            return 2

    machine = StateMachine(StateA.goes_to(StateB))
    await machine.cycle()
    assert machine.value == 2


@pytest.mark.asyncio
async def test_immediate_transition():
    class StateA(State[int]):
        async def enter_state(self):
            return self.cycle()

    class StateB(State[int]):
        async def enter_state(self):
            return

    machine = StateMachine(StateA.goes_to(StateB))
    await machine.cycle()
    assert isinstance(machine.state, StateB)
