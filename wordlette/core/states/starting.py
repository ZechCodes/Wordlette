from bevy import inject, dependency

from wordlette.core.events import StartupEvent
from wordlette.events import EventDispatch
from wordlette.state_machines import State


class Starting(State):
    @inject
    async def enter_state(self, events: EventDispatch = dependency()):
        await events.emit(StartupEvent())
        return self.cycle()
