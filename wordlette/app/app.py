from wordlette.app.app_protocol import AppProtocol
from wordlette.state_machine import StateMachine
from wordlette.app.app_state import AppState
from bevy import Context
from wordlette.smart_functions import call
from typing import Callable, Type, TypeAlias
from starlette.types import Receive, Scope, Send
from starlette.applications import Starlette
from wordlette.exceptions import WordletteNoStarletteAppFound


StateMachineConstructor: TypeAlias = (
    Type[StateMachine]
    | Callable[[AppProtocol], StateMachine]
    | Callable[[], StateMachine]
)
import logging

logger = logging.root.getChild("APP")


class App:
    def __init__(self, state_machine_constructor: StateMachineConstructor = AppState):
        self._app_context = Context.factory()
        self._state = call(state_machine_constructor, self)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if not self.state.started:
            try:
                await self.state.start(self.state.starting, self)
            except Exception:
                logger.exception("ERROR ENCOUNTERED")

        if not self.app:
            raise WordletteNoStarletteAppFound(
                f"Cannot handle {scope['type']=} because the current application state has not added a Starlette app "
                "to the context."
            )

        await self.app(scope, receive, send)

    @property
    def app(self) -> Starlette | None:
        return self.context.find(Starlette)

    @property
    def app_context(self) -> Context:
        return self._app_context

    @property
    def context(self) -> Context:
        return self.state.value

    @property
    def state(self) -> StateMachine:
        return self._state
