from __future__ import annotations
from bevy import Bevy, Context, Inject, bevy_method
from wordlette.state_machine import StateMachine, State
from wordlette.config import Config
from wordlette.wordlette.error_app import create_error_application
from starlette.applications import Starlette
from wordlette.events import EventManager
from dataclasses import dataclass
from typing import Any


@dataclass()
class StateChangeEvent:
    type: str
    old_state: State
    new_state: State
    context: Context
    args: tuple[Any]
    kwargs: dict[str, Any]


class DispatchedStateMachine(StateMachine, Bevy):
    async def _set_current_state(self, new_state, *args, **kwargs):
        old_state = self.state
        await self._dispatch("changing-state", old_state, new_state, args, kwargs)
        context = await super()._set_current_state(new_state, *args, **kwargs)
        await self._dispatch("changed-state", old_state, new_state, args, kwargs)
        return context

    @bevy_method
    async def _dispatch(
        self,
        type: str,
        old_state: State,
        new_state: State,
        args: tuple[Any],
        kwargs: dict[str, Any],
        events: EventManager = Inject,
    ):
        label = {
            "type": type,
            "old-state": old_state,
            "new-state": new_state,
        }
        event = StateChangeEvent(type, old_state, new_state, self.value, args, kwargs)
        await events.dispatch(label, event)


class AppState(DispatchedStateMachine):
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
    async def loading_extensions(self, app):
        context = self.bevy.branch()
        context.add(
            create_error_application("Testing loading extensions", "Testing"),
            use_as=Starlette,
        )
        return context

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
