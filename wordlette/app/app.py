from pathlib import Path
from typing import TypeVar, TypeAlias, Callable, Awaitable

from bevy import get_repository
from starlette.types import Receive, Send, Scope

from wordlette.state_machines import StateMachine

T = TypeVar("T")
_App: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]


class WordletteApp:
    app_settings = {
        "config_file": Path("config.yml"),
    }

    def __init__(self, state_machine: StateMachine[T]):
        self._state_machine: StateMachine = state_machine
        self._router = None

        self.handle_request = self._create_state_machine_then_forward

        get_repository().set(WordletteApp, self)
        get_repository().set(StateMachine, self._state_machine)

    async def handle_lifespan(self, _, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
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

    async def _create_state_machine_then_forward(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await self._state_machine.cycle()

        self.handle_request = self._forward_request

        await self.handle_request(scope, receive, send)

    async def _forward_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await self._router(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self.handle_request(scope, receive, send)
