from bevy import bevy_method, Inject
from pathlib import Path
from starlette.applications import Starlette

from wordlette.extensions.auto_loader import auto_load_directory
from wordlette.extensions.plugins import Plugin
from wordlette.pages import Page
from wordlette.state_machine import State
from wordlette.wordlette.error_app import create_error_application
from .base_app import BaseApp


class BaseAppState(State):
    def __init__(self):
        self.context = self.bevy.branch()


class Starting(BaseAppState):
    async def enter(self):
        """Add a catch-all starlette application that 400's every request to tell the user that something has gone wrong
        with the application routing."""
        self.context.add(
            create_error_application(
                "Wordlette could not find a valid Starlette application to handle request routing.",
                "No Router Found",
            ),
            use_as=Starlette,
        )

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
    async def enter(self):
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
