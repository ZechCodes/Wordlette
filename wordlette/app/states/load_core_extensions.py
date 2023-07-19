import logging

from bevy import inject, dependency

from wordlette.app import WordletteApp
from wordlette.extensions import get_extensions_in_directory, Extension
from wordlette.state_machines import State

logger = logging.getLogger("StateMachine").getChild("LoadCoreExtensions")


class LoadCoreExtensions(State):
    @inject
    async def enter_state(self, app: WordletteApp = dependency()):
        extensions = get_extensions_in_directory(app.app_settings["extensions_dir"])
        self._load_extensions(extensions)
        return self.cycle()

    @inject
    def _load_extension(self, extension: Extension, app: WordletteApp = dependency()):
        try:
            extension_module = extension.load_extension()
        except Exception as e:
            logger.debug(
                f"Failed to load core extension {extension.import_path!r}: {e!r}"
            )
        else:
            app.add_extension(extension.name, extension_module)
            logger.debug(f"Loaded {extension.import_path!r} as a core extension.")

    def _load_extensions(self, extensions: list[Extension]):
        for extension in extensions:
            self._load_extension(extension)
