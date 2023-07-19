from pathlib import Path

from bevy import inject, dependency

from wordlette.app import WordletteApp
from wordlette.configs.managers import ConfigManager
from wordlette.state_machines import State


class LoadingConfig(State):
    @inject
    async def enter_state(
        self, app: WordletteApp = dependency(), config: ConfigManager = dependency()
    ):
        if await self.config_found():
            config.load_config_file(app.app_settings["config_name"], Path())
            print(
                "Config:",
                config.get("hi", list),
            )
            print(
                "Config file",
                config.find_config_file(app.app_settings["config_name"], Path()),
            )

        return self.cycle()

    @staticmethod
    @inject
    async def config_found(
        app: WordletteApp = dependency(), config: ConfigManager = dependency()
    ) -> bool:
        return (
            config.find_config_file(app.app_settings["config_name"], Path()) is not None
        )
