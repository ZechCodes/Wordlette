from logging import getLogger
from pathlib import Path
from types import ModuleType
from typing import TypeVar, TypeAlias, Callable, Awaitable

from bevy import get_repository
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Send, Scope

from wordlette.configs.managers import ConfigManager
from wordlette.state_machines import StateMachine

logger = getLogger(__name__)

T = TypeVar("T")
_App: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]


class WordletteApp:
    app_settings = {
        "config_name": "wordlette-config",
        "extensions_dir": Path("extensions"),
    }

    def __init__(
        self,
        state_machine: StateMachine[T],
        *,
        config_manager: ConfigManager | None = None,
    ):
        self._config_manager = config_manager or ConfigManager()
        self._extensions = {}
        self._router = PlainTextResponse("No router is mounted.", status_code=500)
        self._state_machine: StateMachine = state_machine

        self._update_repository()

    def add_extension(self, name: str, extension_module: ModuleType):
        self._extensions[name] = extension_module

    async def handle_lifespan(self, _, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
                    await self._startup()
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    await send({"type": "lifespan.shutdown.complete"})
                    break

    @property
    def state_machine(self) -> StateMachine:
        return self._state_machine

    def set_router(self, router: _App):
        self._router = router

    def _build_state_machine(self) -> StateMachine:
        from wordlette.cms.states import BootstrapState, ConfigState

        return StateMachine(BootstrapState.goes_to(ConfigState))

    async def _startup(self):
        await self._state_machine.cycle()

    async def handle_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._router(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self.handle_request(scope, receive, send)

    def _update_repository(self):
        get_repository().set(ConfigManager, self._config_manager)
        get_repository().set(StateMachine, self._state_machine)
        get_repository().set(WordletteApp, self)
