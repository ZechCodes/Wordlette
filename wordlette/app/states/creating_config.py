from pathlib import Path

from bevy import inject, dependency
from starlette.responses import PlainTextResponse

from wordlette.app import WordletteApp
from wordlette.configs.managers import ConfigManager
from wordlette.state_machines import State


class CreatingConfig(State):
    @inject
    async def enter_state(
        self, app: WordletteApp = dependency(), config: ConfigManager = dependency()
    ):
        app.set_router(PlainTextResponse("Creating Config File", status_code=200))

    @staticmethod
    @inject
    async def has_no_config_file(
        app: WordletteApp = dependency(), config: ConfigManager = dependency()
    ) -> bool:
        return config.find_config_file(app.app_settings["config_name"], Path()) is None
