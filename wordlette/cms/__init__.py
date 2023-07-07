from typing import Callable, Awaitable, TypeAlias

from starlette.types import Receive, Scope, Send

from wordlette.cms.states import BootstrapState
from wordlette.states.machine import StateMachine

App: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]


def create_cms_app() -> App:
    machine: StateMachine[App] | None = None

    async def forward_request(scope: Scope, receive: Receive, send: Send) -> None:
        nonlocal machine
        if not machine:
            machine = await BootstrapState.start()

        await machine.value(scope, receive, send)

    return forward_request
