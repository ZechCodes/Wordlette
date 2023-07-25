from functools import reduce
from logging import getLogger
from operator import call
from types import ModuleType
from typing import TypeAlias, Callable, Awaitable, Sequence, Type

from bevy import get_repository
from starlette.types import Receive, Send, Scope, Message, ASGIApp

from wordlette.extensions import Extension
from wordlette.middlewares import Middleware

logger = getLogger(__name__)

_MiddlewareConstructor: TypeAlias = Callable[[ASGIApp], Middleware] | Type[Middleware]


class Sender:
    def __init__(self, send: Send):
        self.sent = False
        self.send = send

    def __call__(self, message: Message) -> Awaitable[None]:
        self.sent = True
        return self.send(message)


class WordletteApp:
    def __init__(
        self,
        extensions: Sequence[Callable[[], Extension]] = (),
        middleware: Sequence[_MiddlewareConstructor] = (),
    ):
        self._update_repository()

        self._extensions = self._build_extensions(extensions)
        self._middleware_stack: ASGIApp = self._build_middleware_stack(middleware)

    def add_extension(self, name: str, extension_module: ModuleType):
        self._extensions[name] = extension_module

    async def handle_lifespan(self, _, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    await send({"type": "lifespan.shutdown.complete"})
                    break

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self._middleware_stack(scope, receive, Sender(send))

    async def _500_response(self, scope: Scope, receive: Receive, send: Sender):
        if send.sent:
            return

        await send({"type": "http.response.start", "status": 500})
        await send(
            {
                "type": "http.response.body",
                "body": b"Internal Server Error: No middleware is configured to support this request.",
            }
        )

    def _build_extensions(self, extension_constructors):
        return {
            name: extension for name, extension in map(call, extension_constructors)
        }

    def _build_middleware_stack(self, middleware_constructors):
        return reduce(
            lambda previous, current: current(previous),
            middleware_constructors,
            self._500_response,
        )

    def _update_repository(self):
        get_repository().set(WordletteApp, self)
