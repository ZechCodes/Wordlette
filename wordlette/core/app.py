import logging
from functools import reduce
from types import ModuleType
from typing import TypeAlias, Callable, Awaitable, Sequence, Type, cast

from bevy import get_repository, dependency
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Send, Scope, Message, ASGIApp

from wordlette.configs.managers import ConfigManager
from wordlette.core.events import (
    LifespanStartupEvent,
    LifespanShutdownEvent,
)
from wordlette.core.exceptions import InvalidExtensionOrConstructor
from wordlette.events import EventDispatch
from wordlette.extensions import Extension
from wordlette.middlewares import Middleware
from wordlette.state_machines import StateMachine

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("App")

_MiddlewareConstructor: TypeAlias = Callable[[ASGIApp], Middleware] | Type[Middleware]


@runtime_checkable
class CallableProtocol(Protocol):
    def __call__(self, *args, **kwargs):
        ...


def _create_config_manager():
    from wordlette.configs.json_handlers import JsonHandler
    from wordlette.configs.toml_handlers import TomlHandler
    from wordlette.configs.yaml_handlers import YamlHandler

    manager = ConfigManager([JsonHandler])
    for handler in [TomlHandler, YamlHandler]:
        if handler.supported():
            manager.add_handler(handler)

    return manager


class Sender:
    def __init__(self, send: Send):
        self.sent = False
        self.send = send

    def __call__(self, message: Message) -> Awaitable[None]:
        self.sent = True
        return self.send(message)


class WordletteApp:
    events: EventDispatch = dependency()

    def __init__(
        self,
        *,
        extensions: Sequence[Callable[[], Extension]] = (),
        middleware: Sequence[_MiddlewareConstructor],
        state_machine: StateMachine,
        config_manager: ConfigManager | None = None,
    ):
        self._update_repository()
        self._extensions = self._build_extensions(extensions)
        self._middleware_stack: ASGIApp = self._build_middleware_stack(middleware)
        self._state_machine = state_machine

    @overload
    def add_extension(self, name: str, extension: Extension):
        ...

    @overload
    def add_extension(self, name: str, extension_constructor: Callable[[], Extension]):
        ...

    @overload
    def add_extension(self, extension_constructor: Callable[[], Extension]):
        ...

    @overload
    def add_extension(self, extension: Extension):
        ...

    def add_extension(self, *args):
        match args:
            case (str() as name, Extension() as extension):
                self._extensions[name] = extension

            case (str() as name, CallableProtocol() as extension_constructor):
                self._extensions[name] = extension = extension_constructor()

            case (Extension(name) as extension,):
                self._extensions[name] = extension

            case (CallableProtocol() as extension_constructor,):
                extension = extension_constructor()
                self._extensions[extension.name] = extension

            case _:
                raise InvalidExtensionOrConstructor(
                    "You must pass an extension or an extension constructor, got {args}. A valid constructor can be "
                    "any type or callable that returns an extension object."
                )

        get_repository().set(type(extension), extension)

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send):
        while True:
            match await receive():
                case {"type": "lifespan.startup"}:
                    await self.events.emit(LifespanStartupEvent(scope))
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    await self.events.emit(LifespanShutdownEvent(scope))
                    await send({"type": "lifespan.shutdown.complete"})
                    break

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if not self._state_machine.started:
            await self._state_machine.cycle()

        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                await self._middleware_stack(scope, receive, Sender(send))

    async def _500_response(self, scope: Scope, receive: Receive, send: Sender):
        if send.sent:
            return

        await PlainTextResponse("Internal Server Error", status_code=500)(
            scope, receive, send
        )

    def _build_extensions(self, extension_constructors):
        def create(extension_constructor):
            match extension_constructor:
                case type():
                    return get_repository().get(extension_constructor)

                case _:
                    extension = extension_constructor()
                    get_repository().set(type(extension), extension)
                    return extension

        return {
            name: extension for name, extension in map(create, extension_constructors)
        }

    def _build_middleware_stack(self, middleware_constructors) -> ASGIApp:
        def middleware_factory(previous, current) -> ASGIApp:
            return current(previous)

        return reduce(
            middleware_factory,
            middleware_constructors,
            cast(ASGIApp, self._500_response),
        )

    def _update_repository(self):
        get_repository().set(WordletteApp, self)
