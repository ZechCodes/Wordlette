import bevy
import wordlette.path
from typing import Any, Dict, Tuple


class Plugin(bevy.Bevy):
    ...


class PluginLoader(bevy.Bevy):
    path: wordlette.path.Path

    def __init__(self, name: str, settings: Dict[str, Any]):
        self.name = name
        self._settings = settings
        self._plugin = None

        if self.enabled:
            self.load()

    @property
    def import_from(self) -> Tuple[str]:
        import_from: str = self._settings.get("import", "")
        return tuple(import_from.split(".")) if import_from else (self.path.package, "plugins", self.name)

    @property
    def scope(self) -> Dict[str, Any]:
        return self._settings.get("scope", {})

    @property
    def settings(self) -> Dict[str, Any]:
        return self._settings.get("settings", {})

    @property
    def enabled(self) -> bool:
        return self._settings.get("enabled", False)

    def load(self):
        if self._plugin:
            raise ImportError(f"The plugin '{self.name}' is already loaded")

        if not self.enabled:
            raise ImportError(f"Cannot load the plugin '{self.name}' because it is disabled")

        self._plugin = self.path.importer(*self.import_from)
        if not self._plugin:
            raise ImportError(f"Could not find a module for the plugin '{self.name}'")
