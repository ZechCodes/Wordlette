import bevy
import logging
import os
import pathlib
import starlette.routing
import wordlette.config
import wordlette.database
import wordlette.logging
import wordlette.models
import wordlette.path
import wordlette.plugins
from typing import Any, Dict, List, Optional


class Site(bevy.Bevy):
    db: wordlette.database.Database
    config: wordlette.config.Config
    path: wordlette.path.Path
    plugin_factory: bevy.Factory[wordlette.plugins.PluginLoader]
    log: wordlette.logging.Logging

    def __init__(self, file: str, /):
        self.path.path = file
        self._project_path = pathlib.Path(file).parent
        self._plugins: List[wordlette.plugins.PluginLoader] = []
        self._routes: List[starlette.routing.Route] = []
        self._settings = None

    @property
    def local_path(self) -> pathlib.Path:
        return self._project_path

    def configure(self):
        self.configure_logging()

    def configure_logging(self):
        log_levels = {
            "INFO": logging.INFO,
            "WARN": logging.WARN,
            "DEBUG": logging.DEBUG,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        logging_settings = self._settings.get("logging", {}).copy()
        logging_settings["level"] = log_levels.get(logging_settings.get("level"), logging.INFO)

        logging.basicConfig(**logging_settings)

    def get_env_setting(self, name: str, /, *, default: Optional[Any] = None) -> Any:
        return os.environ.get(name, default)

    def load_settings(self) -> Dict[str, Any]:
        return self.config.get("settings", require=True)

    async def setup(self):
        self._settings = self.load_settings()
        self.configure()
        await self._bootstrap()

    async def _bootstrap(self):
        self.log.debug("Loading plugins")
        plugins = self._settings.get("plugins", {})
        self._load_plugins(plugins)

        self.log.debug("Connecting to database")
        await self.db.connect(self._get_db_config([]))

    def _get_db_config(self, models: List[str]) -> Dict[str, Any]:
        host = self.get_env_setting("DB_HOST", default="localhost")
        port = self.get_env_setting("DB_PORT", default="5432")
        user = self.get_env_setting("DB_USER", default="postgresadmin")
        password = self.get_env_setting("DB_PASS", default="dev-env-password-safe-to-be-public")
        database = self.get_env_setting("DB_NAME", default="bpydb")
        self.log.debug(
            f"DB Connection Details -> {user}:****@{host}:{port}/{database}"
        )
        return {
            "connections": {
                "wordlette": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": host,
                        "port": port,
                        "user": user,
                        "password": password,
                        "database": database
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
