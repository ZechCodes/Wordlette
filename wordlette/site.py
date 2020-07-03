import bevy
import os
import pathlib
import starlette.routing
import wordlette.config
import wordlette.database
import wordlette.models
import wordlette.path
import wordlette.plugins
from typing import Any, Dict, List, Optional


class Site(bevy.Bevy):
    db: wordlette.database.Database
    config: wordlette.config.Config
    path: wordlette.path.Path
    plugin_factory: bevy.Factory[wordlette.plugins.PluginLoader]

    def __init__(self, file: str, /):
        self.path.path = file
        self._project_path = pathlib.Path(file).parent
        self._plugins: List[wordlette.plugins.PluginLoader] = []
        self._routes: List[starlette.routing.Route] = []

    @property
    def local_path(self) -> pathlib.Path:
        return self._project_path

    async def setup(self):
        await self._bootstrap()

    def get_env_setting(self, name: str, /, *, default: Optional[Any] = None) -> Any:
        return os.environ.get(name, default)

    async def _bootstrap(self):
        """ Load the site settings before attempting to load anything else. """
        await self.db.connect(
            self._get_db_config([])
        )

        plugins = self.config.get("settings", {}, require=True).get("plugins", {})
        self._load_plugins(plugins)

    def _get_db_config(self, models: List[str]) -> Dict[str, Any]:
        return {
            "connections": {
                "wordlette": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.get_env_setting("DB_HOST", default="localhost"),
                        "port": self.get_env_setting("DB_PORT", default="5432"),
                        "user": self.get_env_setting("DB_USER", default="postgresadmin"),
                        "password": self.get_env_setting("DB_PASS", default="dev-env-password-safe-to-be-public"),
                        "database": self.get_env_setting("DB_NAME", default="bpydb"),
                    }
                },
            },
            "apps": {
                "models": {
                    "models": models,
                    "default_connection": "wordlette",
                }
            }
        }

    def _load_plugins(self, plugins: Dict[str, Dict[str, Any]]):
        for name, settings in plugins.items():
            self.plugin_factory(name, settings)
