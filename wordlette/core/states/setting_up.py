from bevy import inject, dependency

from wordlette.core import WordletteApp
from wordlette.state_machines import State
from wordlette.state_machines.states import RequestCycle


class SettingUp(State):
    @inject
    async def enter_state(
        self, app: WordletteApp = dependency()
    ) -> RequestCycle | None:
        ...

    @classmethod
    async def needs_setup(cls) -> bool:
        return False