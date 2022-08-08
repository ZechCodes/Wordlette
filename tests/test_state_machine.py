import pytest
from wordlette.state.state import State
from wordlette.state import StateMachine
from wordlette.exceptions import (
    WordletteTransitionImpossible,
    WordletteTransitionFailed,
    WordletteDeadendState,
    WordletteNoSuchState,
)


@pytest.mark.asyncio
async def test_successful_state_transition():
    a = State("A")
    b = State("B")
    ran = False

    def transition():
        nonlocal ran
        ran = True

    a.add_transition(b, transition)
    await a.transition(b)
    assert ran


@pytest.mark.asyncio
async def test_unsuccessful_state_no_transition():
    a = State("A")
    b = State("B")
    with pytest.raises(WordletteTransitionImpossible):
        await a.transition(b)


@pytest.mark.asyncio
async def test_unsuccessful_state_failed_transition():
    a = State("A")
    b = State("B")

    def transition():
        raise RuntimeError("TESTING")

    a.add_transition(b, transition)
    with pytest.raises(WordletteTransitionFailed):
        await a.transition(b)


@pytest.mark.asyncio
async def test_state_entered():
    was_entered = False

    async def entered():
        nonlocal was_entered
        was_entered = True

    a = State("A")
    b = State("B", entered)

    a.add_transition(b, lambda: ...)
    await a.transition(b)
    assert was_entered


@pytest.mark.asyncio
async def test_transition_params():
    a = State("A")
    b = State("B")
    state = None

    def transition_a(to_state: State):
        nonlocal state
        state = to_state

    a.add_transition(b, transition_a)
    await a.transition(b)
    assert state is b

    state = None

    def transition_b(from_state: State):
        nonlocal state
        state = from_state

    b.add_transition(a, transition_b)
    await b.transition(a)
    assert state is b


@pytest.mark.asyncio
async def test_state_machine():
    machine = StateMachine("test_machine", "STATE_A")
    machine.add_transitions("STATE_A", STATE_B=lambda: ...)
    machine.add_transitions("STATE_B", STATE_A=lambda: ...)
    await machine.transition("STATE_B")
    assert machine.state == "STATE_B"


@pytest.mark.asyncio
async def test_state_machine_deadend_state():
    machine = StateMachine("test_machine", "STATE_A")
    machine.add_transitions("STATE_A", STATE_B=lambda: ...)
    with pytest.raises(WordletteDeadendState):
        await machine.transition("STATE_B")


@pytest.mark.asyncio
async def test_state_machine_no_such_state():
    machine = StateMachine("test_machine", "STATE_A")
    with pytest.raises(WordletteNoSuchState):
        await machine.transition("STATE_B")


@pytest.mark.asyncio
async def test_state_machine_enter_transitions():
    was_entered = False

    def entered():
        nonlocal was_entered
        was_entered = True

    machine = StateMachine("test_machine", "STATE_A")
    machine.create_state("STATE_B", entered)
    machine.add_transitions("STATE_A", STATE_B=lambda: ...)
    machine.add_transitions("STATE_B", STATE_A=lambda: ...)
    await machine.transition("STATE_B")
    assert was_entered
