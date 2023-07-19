from bevy import inject, dependency
from starlette.responses import PlainTextResponse

from wordlette.app import WordletteApp
from wordlette.state_machines import State


class CreatingConfig(State):
    @inject
    async def enter_state(self, app: WordletteApp = dependency()):
        if not await self.no_config_found():
            return self.cycle()

        app.set_router(PlainTextResponse("Creating Config File", status_code=200))

    @staticmethod
    @inject
    async def no_config_found(app: WordletteApp = dependency()) -> bool:
        return not app.app_settings["config_file"].exists()
