from wordlette.state.state import State, Transition
from wordlette.exceptions import WordletteDeadendState, WordletteNoSuchState


class StateMachine:
    def __init__(self, name: str, default_state_name: str):
        self._name = name
        self._states: dict[str, State] = {}
        self._state = self._get_state_or_create(default_state_name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> str:
        return self._state.name

    def add_transitions(self, state_name: str, **transitions: Transition):
        """Adds transitions to a state. This will handle the process of creating states if they do not exist."""
        state = self._get_state_or_create(state_name)
        for to_state_name, transition in transitions.items():
            state.add_transition(self._get_state_or_create(to_state_name), transition)

    def create_state(self, state_name: str, enter_transition: Transition | None = None):
        self._states[state_name] = State(state_name, enter_transition)

    async def transition_to(self, state_name: str):
        """Transitions from the current state to the requested state.

        Raises WordletteDeadendState if the requested state has no transitions.
        Raises WordletteNoSuchState if the requested state does not exist.
        Raises all exceptions that wordlette.state.state.State.transition can raise.
        """
        if state_name not in self._states:
            raise WordletteNoSuchState(f"{self} has no state named {state_name!r}")

        state = self._states[state_name]
        if state.deadend:
            raise WordletteDeadendState(
                f"{self} cannot transition to {state} because it has no transitions"
            )

        await self._state.transition_to(state)
        self._state = state

    def _get_state_or_create(self, state_name: str) -> State:
        if state_name not in self._states:
            self.create_state(state_name)

        return self._states[state_name]

    def __repr__(self):
        args = [f"{self.name!r}"]
        args.extend(f"{name}={value}" for name, value in self._states.items())
        return f"{type(self).__name__}({', '.join(args)})"
