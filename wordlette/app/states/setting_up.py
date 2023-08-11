from bevy import inject, dependency

from wordlette.app import WordletteApp
from wordlette.state_machines import State
from wordlette.state_machines.states import RequestCycle


class SettingUp(State):
    @inject
    async def enter_state(
        self, app: WordletteApp = dependency()
    ) -> RequestCycle | None:
        ...

    async def needs_setup(self) -> bool:
        return False
