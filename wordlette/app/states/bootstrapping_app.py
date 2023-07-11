from bevy import inject, dependency
from starlette.responses import PlainTextResponse

from wordlette.app import WordletteApp
from wordlette.state_machines import State


class BootstrappingApp(State):
    @inject
    async def enter_state(self, app: WordletteApp = dependency()):
        app.set_router(PlainTextResponse("Wordlette is starting.", status_code=200))
        return self.cycle()

    @staticmethod
    @inject
    async def no_config_found(app: WordletteApp = dependency()) -> bool:
        return not app.app_settings["config_file"].exists()

    @staticmethod
    async def has_database_config() -> bool:
        return not await BootstrappingApp.no_config_found()
