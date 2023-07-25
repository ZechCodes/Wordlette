from functools import reduce
from logging import getLogger
from operator import call
from types import ModuleType
from typing import TypeAlias, Callable, Awaitable, Sequence, Type

from bevy import get_repository

from wordlette.extensions import Extension

logger = getLogger(__name__)

_ASGIApp: TypeAlias = Callable[[Scope, Receive, Send], Awaitable[None]]




class WordletteApp:
    def __init__(
        self,
        extensions: Sequence[Callable[[], Extension]] = (),
    ):
        self._update_repository()

        self._extensions = self._build_extensions(extensions)

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

    async def handle_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._router(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self.handle_request(scope, receive, send)

    def _update_repository(self):
        get_repository().set(WordletteApp, self)

    def _build_extensions(self, extension_constructors):
        return {
            name: extension for name, extension in map(call, extension_constructors)
        }
