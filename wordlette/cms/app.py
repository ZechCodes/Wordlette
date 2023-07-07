from typing import TypeAlias, Callable, Awaitable

from starlette.types import Receive, Scope, Send

from wordlette.cms.states import BootstrapState
from wordlette.states.machine import StateMachine

App: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]


class CMSApp:
    def __init__(self):
        self._state_machine: StateMachine | None = None
        self.handle_request = self._create_state_machine_then_forward

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    await send({"type": "lifespan.shutdown.complete"})
                    break

    async def _create_state_machine_then_forward(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        self._state_machine = await BootstrapState.start()
        self.handle_request = self._forward_request

        await self.handle_request(scope, receive, send)

    async def _forward_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await self._state_machine.value(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self.handle_request(scope, receive, send)
