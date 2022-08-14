import pytest
import pytest_asyncio
from wordlette.state_machine import StateMachine, state
from wordlette.exceptions import (
    WordletteTransitionImpossible,
    WordletteTransitionFailed,
)


@pytest_asyncio.fixture()
async def two_state_machine():
    class Machine(StateMachine):
        def __init__(self, *args):
            super().__init__(*args)
            self.result = []

        @state
        def state_a(self):
            self.result.append("state_a_run")

        @state
        def state_b(self):
            self.result.append("state_b_run")

        @state_a >> state_b
        def transition_a_to_b(self):
            self.result.append("a_to_b")

        @state_b >> state_a
        def transition_b_to_a(self):
            self.result.append("b_to_a")

    return await Machine(Machine.state_a)


@pytest_asyncio.fixture()
async def two_state_failure_machine():
    class Machine(StateMachine):
        fail_a = state()
        fail_b = state()

        @fail_a >> fail_b
        def transition_a_to_b(self):
            raise Exception()

    return await Machine(Machine.fail_a)


@pytest.mark.asyncio
async def test_state_machine(two_state_machine):
    await two_state_machine.to(two_state_machine.state_b)
    await two_state_machine.to(two_state_machine.state_a)
    assert two_state_machine.result == [
        "state_a_run",
        "a_to_b",
        "state_b_run",
        "b_to_a",
        "state_a_run",
    ]


@pytest.mark.asyncio
async def test_unsuccessful_state_no_transition(two_state_machine):
    with pytest.raises(WordletteTransitionImpossible):
        await two_state_machine.to(two_state_machine.state_a)


@pytest.mark.asyncio
async def test_transition_failure(two_state_failure_machine):
    with pytest.raises(WordletteTransitionFailed):
        await two_state_failure_machine.to(two_state_failure_machine.fail_b)
