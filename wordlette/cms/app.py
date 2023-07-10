from typing import TypeAlias, Callable, Awaitable

from bevy import get_repository
from starlette.types import Receive, Scope, Send

from wordlette.state_machines.machine import StateMachine

App: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]


class CMSApp:
    def __init__(self):
        self._state_machine: StateMachine | None = None
        self.handle_request = self._create_state_machine_then_forward
        self._router = None

        get_repository().set(CMSApp, self)

    async def handle_lifespan(self, _, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    await send({"type": "lifespan.shutdown.complete"})
                    break

    def set_router(self, router: App):
        self._router = router

    def _build_state_machine(self) -> StateMachine:
        from wordlette.cms.states import BootstrapState, ConfigState

        return StateMachine(BootstrapState.goes_to(ConfigState))

    async def _create_state_machine_then_forward(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        self._state_machine = self._build_state_machine()
        get_repository().set(StateMachine, self._state_machine)

        await self._state_machine.cycle()
        print(self._state_machine.state)

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
