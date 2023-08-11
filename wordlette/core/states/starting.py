from bevy import inject

from wordlette.core.events import StartupEvent
from wordlette.events import Observable
from wordlette.state_machines import State


class Starting(State, Observable):
    @inject
    async def enter_state(self):
        await self.emit(StartupEvent())
        return self.cycle()
