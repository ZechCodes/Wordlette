from wordlette.state_machines import State


class Starting(State):
    async def enter_state(self):
        return self.cycle()
