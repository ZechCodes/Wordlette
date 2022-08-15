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

        @state_a.goes_to(state_b).when
        async def transition_a_to_b(self, value):
            if value == "b":
                self.result.append("a_to_b")
                return True

            return False

        @state_b.goes_to(state_a).when
        async def transition_b_to_a(self, value):
            if value == "a":
                self.result.append("b_to_a")
                return True

            return False

    return await Machine().start(Machine.state_a, "")


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


@pytest.mark.asyncio
async def test_aggregate_transitions():
    states = []

    class TestMachine(StateMachine):
        @State
        async def A(self, arg):
            states.append("A")

        @State
        async def B(self, arg):
            states.append("B")

        @State
        async def C(self, arg):
            states.append("C")

        @ (A & B).goes_to(C).when
        async def arg_is_c(self, arg):
            return arg == "C"

        C.goes_to(B)

    machine = TestMachine()
    await machine.start(TestMachine.A, "STARTING")
    await machine.next("C")
    await machine.next("B")
    await machine.next("C")
    assert states == ["A", "C", "B", "C"]


@pytest.mark.asyncio
async def test_aggregate_transitions():
    states = []

    class TestMachine(StateMachine):
        @State
        async def A(self, arg):
            states.append("A")

        @State
        async def B(self, arg):
            states.append("B")

        @State
        async def C(self, arg):
            states.append("C")

        @ (A & B).goes_to(C).when
        async def arg_is_c(self, arg):
            return arg == "C"

        C.goes_to(B)

    machine = TestMachine()
    await machine.start(TestMachine.A, "STARTING")
    await machine.next("C")
    await machine.next("B")
    await machine.next("C")
    assert states == ["A", "C", "B", "C"]


@pytest.mark.asyncio
async def test_default_transitions():
    states = []

    class TestMachine(StateMachine):
        @State
        async def A(self, arg):
            states.append("A")

        @State
        async def B(self, arg):
            states.append("B")

        @State
        async def C(self, arg):
            states.append("C")

        @ (A & B).goes_to(C).when
        async def arg_is_c(self, arg):
            return arg == "C"

        C.goes_to(B)
        A.goes_to(B)
        B.goes_to(A)

    machine = TestMachine()
    await machine.start(TestMachine.A, "STARTING")
    await machine.next("GO TO B")  # At A, will go to B
    await machine.next("GO TO A")  # At B, will go to A
    await machine.next("C")  # At A, will go to C
    await machine.next("GO TO B")  # At C, will go to B
    await machine.next("C")  # At B, will go to C
    assert states == ["A", "B", "A", "C", "B", "C"]
