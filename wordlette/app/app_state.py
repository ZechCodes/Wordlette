from __future__ import annotations

from bevy import Inject, bevy_method
from pathlib import Path
from starlette.applications import Starlette

from wordlette.extensions.auto_loader import auto_load_directory
from wordlette.pages import Page
from wordlette.state_machine import StateMachine, State
from wordlette.wordlette.error_app import create_error_application


class SiteConfig:
    ...


Database = DatabaseConfig = SiteConfig


class AppState(StateMachine):
    @State
    async def starting(self, app):
        # Add a catch-all starlette application that 400's every request to tell the user that something has gone
        # wrong with the application routing.
        self.bevy.add(
            create_error_application(
                "Wordlette could not find a valid Starlette application to handle request routing.",
                "No Router Found",
            ),
            use_as=Starlette,
        )
        return await self.next(app)

    @State
    async def loading_app_plugins(self, app):
        context = self.bevy.branch()
        context.add(
            create_error_application("Testing loading extensions", "Testing"),
            use_as=Starlette,
        )
        app_plugins_directory = Path("app_plugins").resolve()
        if app_plugins_directory.exists():
            app_plugins = dict(auto_load_directory(app_plugins_directory, []))
            print("Loaded app plugins:", *app_plugins.keys())

        else:
            print("No app plugins to load")

        return await self.next(app)

    @State
    async def creating_site_config(self, app):
        return await self.next(app)

    @State
    async def creating_db_config(self, app):
        return await self.next(app)

    @State
    async def connecting_db(self, app):
        return await self.next(app)

    @State
    async def serving_site(self, app):
        site = Starlette()
        context = self.bevy.branch()
        context.add(site, use_as=Starlette)

        pages_directory = Path("pages").resolve()
        if pages_directory.exists():
            page_extensions = dict(auto_load_directory(pages_directory, [Page]))
            for extension in page_extensions.values():
                for page in extension.found_classes[Page]:
                    page.register(site)

        else:
            print("No pages to load")

        return context

    @State
    async def shutting_down(self):
        ...

    starting.goes_to(loading_app_plugins)

    @loading_app_plugins.goes_to(creating_site_config).when
    @bevy_method
    async def site_config_is_incomplete(self, site_config: SiteConfig = Inject) -> bool:
        return False and site_config.has_missing_values

    @ (loading_app_plugins & creating_site_config).goes_to(creating_db_config).when
    @bevy_method
    async def db_config_is_incomplete(self, db_config: DatabaseConfig = Inject) -> bool:
        return False and db_config.has_missing_values

    (loading_app_plugins & creating_site_config & creating_db_config).goes_to(
        connecting_db
    )

    @connecting_db.goes_to(creating_db_config).when
    @bevy_method
    async def database_failed_to_connect(self, database: Database = Inject) -> bool:
        return False and database.failed_to_connect

    connecting_db.goes_to(serving_site)
    serving_site.goes_to(shutting_down)
