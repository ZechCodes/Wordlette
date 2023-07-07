from wordlette.states import State


class ConfigState(State):
    async def enter_state(self):
        self.value = self._state_machine.state.value
