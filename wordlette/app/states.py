import os
from dataclasses import dataclass
from itertools import compress
from pathlib import Path
from starlette.applications import Starlette
from typing import Type

import wordlette.config.json_loader as json_loader
import wordlette.config.toml_loader as toml_loader
import wordlette.config.yaml_loader as yaml_loader
from bevy import bevy_method, Inject
from wordlette.config.config import Config
from wordlette.databases import Database
from wordlette.exceptions import WordletteNoDatabaseDriverFound
from wordlette.extensions.auto_loader import auto_load_directory, import_package
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.settings import Settings
from wordlette.state_machine import State
from wordlette.wordlette.error_app import create_error_application
from .base_app import BaseApp


@dataclass
class DBEngineImportConfig:
    __config_table__ = "db"

    engine_import: str


class BaseAppState(State):
    def __init__(self):
        self.context = self.bevy.branch()


class Starting(BaseAppState):
    @bevy_method
    async def enter(self, settings: Settings = Inject):
        """Add a catch-all starlette application that 400's every request to tell the user that something has gone wrong
        with the application routing."""
        dev_var = os.getenv("WORDLETTE_DEV", "")
        settings["dev"] = dev_var.casefold() not in {"false", "no", "0"}
        return True

    async def next_state(self):
        return LoadingAppPlugins


class LoadingAppPlugins(BaseAppState):
    @bevy_method
    async def enter(self, app: BaseApp = Inject):
        self.context.add(
            create_error_application("Testing loading extensions", "Testing"),
            use_as=Starlette,
        )
        app_plugins_directory = Path("app_plugins").resolve()
        if app_plugins_directory.exists():
            for module, extension_info in auto_load_directory(
                app_plugins_directory, [Plugin]
            ):
                app.load_app_extension(extension_info)

        return True

    async def next_state(self):
        return LoadingConfig


class LoadingConfig(BaseAppState):
    @bevy_method
    async def enter(self, settings: Settings = Inject, config: Config = Inject):
        # Add file type loaders that have the necessary modules installed
        settings["file_loaders"] = list(
            compress(
                [
                    yaml_loader.YamlFileLoader,
                    toml_loader.TomlFileLoader,
                    json_loader.JsonFileLoader,
                ],
                [yaml_loader.yaml, toml_loader.toml, json_loader.json],
            )
        )
        await config.load_config()
        return True

    async def next_state(self):
        return ConnectingDB


class CreatingConfig(BaseAppState):
    async def enter(self):
        return True

    async def next_state(self):
        return LoadingConfig


class ConnectingDB(BaseAppState):
    @bevy_method
    async def enter(self, db_config: DBEngineImportConfig = Inject):
        db_package_info = import_package(db_config.engine_import, [Database])
        if not db_package_info.found_classes[Database]:
            raise WordletteNoDatabaseDriverFound(
                "Unable to find a database driver to connect to the database."
            )

        await self.connect_db(db_package_info.found_classes[Database].pop())
        return True

    async def connect_db(self, engine_type: Type[Database]):
        engine: Database = self.bevy.create(engine_type, cache=True)
        await engine.connect()

    @staticmethod
    async def on_error(exception: Exception) -> Type[State] | None:
        match exception:
            case ModuleNotFoundError():
                print(f"Could not find the database driver extension: {exception!r}")
                return ConfiguringDB

            case WordletteNoDatabaseDriverFound():
                print(
                    f"Could not find a database driver type in the database driver extension: {exception!r}"
                )
                return ConfiguringDB

    async def next_state(self):
        return LoadingPlugins


class ConfiguringDB(BaseAppState):
    async def enter(self):
        return False

    async def next_state(self):
        return ConnectingDB


class LoadingPlugins(BaseAppState):
    async def enter(self):
        return True

    async def next_state(self):
        return ServingSite


class ServingSite(BaseAppState):
    async def enter(self):
        site = Starlette()
        self.context.add(site, use_as=Starlette)
        pages_directory = Path("pages").resolve()
        if pages_directory.exists():
            page_extensions = dict(auto_load_directory(pages_directory, [Page]))
            for extension in page_extensions.values():
                for page in extension.found_classes[Page]:
                    page.register(site, self.context)

        else:
            print("No pages to load")

    async def next_state(self):
        return ShuttingDown


class ShuttingDown(BaseAppState):
    async def enter(self):
        self.context.add(
            create_error_application(
                "Wordlette has shut down. There is no active router to serve content.",
                "Server Shut Down",
            ),
            use_as=Starlette,
        )

        return True

    async def next_state(self):
        return type(self)
