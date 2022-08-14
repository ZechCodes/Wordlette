import pytest
import pytest_asyncio
from wordlette.state_machine import StateMachine, State
from wordlette.exceptions import WordletteNoTransitionFound


@pytest_asyncio.fixture()
async def two_state_machine():
    class Machine(StateMachine):
        def __init__(self):
            super().__init__()
            self.result = []

        @State
        async def state_a(self, value):
            self.result.append("state_a_run")

        @State
        async def state_b(self, value):
            self.result.append("state_b_run")

        @state_a >> state_b
        async def transition_a_to_b(self, value):
            if value == "b":
                self.result.append("a_to_b")
                return True

            return False

        @state_b >> state_a
        async def transition_b_to_a(self, value):
            if value == "a":
                self.result.append("b_to_a")
                return True

            return False

    return await Machine().start(Machine.state_a, "")


@pytest_asyncio.fixture()
async def two_state_failure_machine():
    class Machine(StateMachine):
        @State
        async def fail_a(self, value):
            ...

        @State
        async def fail_b(self, value):
            ...

        @fail_a >> fail_b
        async def transition_a_to_b(self, value):
            raise Exception()

    return await Machine().start(Machine.fail_a, "")


@pytest.mark.asyncio
async def test_state_machine(two_state_machine):
    await two_state_machine.next("b")
    await two_state_machine.next("a")
    assert two_state_machine.result == [
        "state_a_run",
        "a_to_b",
        "state_b_run",
        "b_to_a",
        "state_a_run",
    ]


@pytest.mark.asyncio
async def test_unsuccessful_state_no_transition(two_state_machine):
    with pytest.raises(WordletteNoTransitionFound):
        await two_state_machine.next("a")
