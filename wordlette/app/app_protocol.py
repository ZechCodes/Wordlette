from typing import Protocol, runtime_checkable
from wordlette.state_machine import StateMachine
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send
from bevy import Context


@runtime_checkable
class AppProtocol(Protocol):
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """This handles events and requests from the ASGI server. This should use the context set by the current
        state."""
        ...

    @property
    def app(self) -> Starlette | None:
        """This should be the Starlette app that the current state has set."""
        ...

    @property
    def app_context(self) -> Context:
        """The app context should contain any application state that should be used globally across all objects. This
        could include configs that should only be loaded at startup."""
        ...

    @property
    def state(self) -> StateMachine[Context, None]:
        """This is the application state machine, it is responsible for building Bevy contexts that inherit from the app
        context. This is useful for switching out interface implementations depending on the current state of the
        application. This might include providing a custom router for setting up the website when it's first been
        installed."""
        ...

    @property
    def context(self) -> Context:
        """References the current context being provided by the application state machine. This context should inherit
        from the app context to provide access to implementations that are persistent across the application's lifetime.
        Each state context will only be guaranteed to be persistent while the application remains in that state."""
        ...
