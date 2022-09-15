import os
from bevy import bevy_method, Inject
from itertools import compress
from pathlib import Path
from starlette.applications import Starlette

import wordlette.config.json_loader as json_loader
import wordlette.config.toml_loader as toml_loader
import wordlette.config.yaml_loader as yaml_loader
from wordlette.config.config import Config
from wordlette.extensions.auto_loader import auto_load_directory
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.settings import Settings
from wordlette.state_machine import State
from wordlette.wordlette.error_app import create_error_application
from .base_app import BaseApp


class BaseAppState(State):
    def __init__(self):
        self.context = self.bevy.branch()


class Starting(BaseAppState):
    @bevy_method
    async def enter(self, settings: Settings = Inject):
        """Add a catch-all starlette application that 400's every request to tell the user that something has gone wrong
        with the application routing."""
        self.context.add(
            create_error_application(
                "Wordlette could not find a valid Starlette application to handle request routing.",
                "No Router Found",
            ),
            use_as=Starlette,
        )

        dev_var = os.getenv("WORDLETTE_DEV", "")
        settings["dev"] = dev_var.casefold() not in {"false", "no", "0"}
        return True

    async def next(self):
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

    async def next(self):
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

    async def next(self):
        return ConnectingDB


class CreatingConfig(BaseAppState):
    async def enter(self):
        return True

    async def next(self):
        return LoadingConfig


class ConnectingDB(BaseAppState):
    async def enter(self):
        return True

    async def next(self):
        return LoadingPlugins


class ConfiguringDB(BaseAppState):
    async def enter(self):
        return True

    async def next(self):
        return ConnectingDB


class LoadingPlugins(BaseAppState):
    async def enter(self):
        return True

    async def next(self):
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

    async def next(self):
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

    async def next(self):
        return type(self)
