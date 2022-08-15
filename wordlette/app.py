from bevy import Bevy, Inject
from bevy.providers.function_provider import bevy_method
from wordlette.state_machine import StateMachine, State
from wordlette.config import Config


class App(StateMachine, Bevy):
    @State
    async def starting(self):
        ...

    @State
    async def loading_extensions(self):
        ...

    @State
    async def creating_site_config(self):
        ...

    @State
    async def creating_db_config(self):
        ...

    @State
    async def connecting_db(self):
        ...

    @State
    async def serving_site(self):
        ...

    @State
    async def shutting_down(self):
        ...

    starting.goes_to(loading_extensions)

    @loading_extensions.goes_to(creating_site_config).when
    @bevy_method
    async def site_config_is_incomplete(self, site_config: SiteConfig = Inject) -> bool:
        return site_config.has_missing_values

    @ (loading_extensions & creating_site_config).goes_to(creating_db_config).when
    @bevy_method
    async def db_config_is_incomplete(self, db_config: DatabaseConfig = Inject) -> bool:
        return db_config.has_missing_values

    (loading_extensions & creating_site_config & creating_db_config).goes_to(
        connecting_db
    )

    @connecting_db.goes_to(creating_db_config).when
    @bevy_method
    async def database_failed_to_connect(self, database: Database = Inject) -> bool:
        return database.failed_to_connect

    connecting_db.goes_to(serving_site)
    serving_site.goes_to(shutting_down)
