import pytest
import pytest_asyncio

from bevy import bevy_method, Context, Inject
from wordlette.exceptions import WordletteStateMachineAlreadyStarted
from wordlette.state_machine import StateMachine, State
from wordlette.state_machine.machine import StateChangeEvent


class LoggedStateMachine(StateMachine):
    def __init__(self):
        super(LoggedStateMachine, self).__init__()
        self.state_history = []


async def _create_machine(state):
    context = Context.factory()
    machine = context.create(LoggedStateMachine, cache=True)
    await machine.start(state)
    return machine


@pytest_asyncio.fixture()
async def two_state_machine():
    class StateA(State):
        @bevy_method
        async def enter(self, machine: LoggedStateMachine = Inject):
            machine.state_history.append("StateA")

        async def next_state(self):
            return StateB

    class StateB(State):
        @bevy_method
        async def enter(self, machine: LoggedStateMachine = Inject):
            machine.state_history.append("StateB")

        async def next_state(self):
            return StateA

    return await _create_machine(StateA)


@pytest_asyncio.fixture()
async def immediate_transition_machine():
    class StateA(State):
        @bevy_method
        async def enter(self, machine: LoggedStateMachine = Inject):
            machine.state_history.append("StateA")
            return True

        async def next_state(self):
            return StateB

    class StateB(State):
        @bevy_method
        async def enter(self, machine: LoggedStateMachine = Inject):
            machine.state_history.append("StateB")

        async def next_state(self):
            return StateA

    return await _create_machine(StateA)


@pytest.mark.asyncio
async def test_state_machine(two_state_machine):
    await two_state_machine.next_state()
    await two_state_machine.next_state()
    assert two_state_machine.state_history == ["StateA", "StateB", "StateA"]


@pytest.mark.asyncio
async def test_repeated_start_attempt(two_state_machine):
    with pytest.raises(WordletteStateMachineAlreadyStarted):
        await two_state_machine.start(...)


@pytest.mark.asyncio
async def test_immediate_transitions(immediate_transition_machine):
    assert immediate_transition_machine.state_history == ["StateA", "StateB"]


@pytest.mark.asyncio
async def test_event_dispatch(immediate_transition_machine: LoggedStateMachine):
    event_history = []

    async def transition_event(payload: StateChangeEvent):
        event_history.append(f"Transition {payload.new_state.name}")

    async def entered_event(payload: StateChangeEvent):
        event_history.append(f"Entered {payload.new_state.name}")

    immediate_transition_machine.on("entered-state", entered_event)
    immediate_transition_machine.on("transitioned-to-state", transition_event)

    await immediate_transition_machine.next()
    await immediate_transition_machine.next()
    assert event_history == [
        "Transition StateA",
        "Transition StateB",
        "Entered StateB",
        "Transition StateA",
        "Transition StateB",
        "Entered StateB",
    ]
