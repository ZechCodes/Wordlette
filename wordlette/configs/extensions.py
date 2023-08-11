from pathlib import Path

from bevy import get_repository

from wordlette.configs.managers import ConfigManager
from wordlette.core.events import StartupEvent
from wordlette.events import Observer
from wordlette.extensions import Extension


def _create_config_manager():
    from wordlette.configs import JsonHandler, TomlHandler, YamlHandler

    manager = ConfigManager([JsonHandler])
    for handler in [TomlHandler, YamlHandler]:
        if handler.supported():
            manager.add_handler(handler)

    return manager


class Config(Extension, Observer):
    def __init__(self, config_manager: ConfigManager | None = None):
        super().__init__()
        self._config_manager = config_manager or _create_config_manager()
        self.config_file_stem = "wordlette.config"
        self.config_directory = Path.cwd()

        get_repository().set(ConfigManager, self._config_manager)

    async def on_startup(self, _: StartupEvent):
        self._config_manager.load_config_file(
            self.config_file_stem, self.config_directory
        )
