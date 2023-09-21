import logging
from functools import reduce, partial
from pathlib import Path
from typing import (
    TypeAlias,
    Callable,
    Awaitable,
    Sequence,
    Type,
    cast,
    overload,
    runtime_checkable,
    Protocol,
    Any,
)

from bevy import get_repository, dependency, inject
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Send, Scope, Message, ASGIApp

from wordlette.core.events import (
    LifespanStartupEvent,
    LifespanShutdownEvent,
)
from wordlette.core.exceptions import InvalidExtensionOrConstructor
from wordlette.events import Observer, Observable
from wordlette.extensions import Extension
from wordlette.middlewares import Middleware
from wordlette.state_machines import StateMachine
from wordlette.utils.apply import apply
from wordlette.utils.at_annotateds import AtAnnotation, AtProvider
from wordlette.utils.options import Null

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("App")

_MiddlewareConstructor: TypeAlias = Callable[[ASGIApp], Middleware] | Type[Middleware]


@runtime_checkable
class CallableProtocol(Protocol):
    def __call__(self, *args, **kwargs):
        ...


class Sender:
    def __init__(self, send: Send):
        self.sent = False
        self.send = send

    def __call__(self, message: Message) -> Awaitable[None]:
        self.sent = True
        return self.send(message)


class WordletteApp(Observable):
    def __init__(
        self,
        *,
        extensions: Sequence[Callable[[], Extension]] = (),
        middleware: Sequence[_MiddlewareConstructor],
        settings: dict[str, Any] | None = None,
        state_machine: StateMachine,
    ):
        self._setup_repository()
        self._extensions: dict[str, Extension] = {}
        self._middleware_stack: ASGIApp = self._build_middleware_stack(middleware)
        self._state_machine = state_machine
        self.settings = self._set_settings_defaults(settings or {})

        self._state_machine.__event_dispatch__.propagate_to(
            self.__event_dispatch__.emit
        )
        self._build_extensions(extensions)

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
                pass

            case (str() as name, CallableProtocol() as extension_constructor):
                extension = extension_constructor()

            case (Extension(name) as extension,):
                pass

            case (CallableProtocol() as extension_constructor,):
                extension = extension_constructor()
                name = extension.name

            case _:
                raise InvalidExtensionOrConstructor(
                    "You must pass an extension or an extension constructor, got {args}. A valid constructor can be "
                    "any type or callable that returns an extension object."
                )

        self._add_extension(name, extension)

    async def handle_lifespan(self, scope: Scope, receive: Receive, send: Send):
        running = True
        while running:
            match await receive():
                case {"type": "lifespan.startup"}:
                    logger.debug("Lifespan startup event")
                    await self.emit(LifespanStartupEvent(scope))
                    await send({"type": "lifespan.startup.complete"})

                case {"type": "lifespan.shutdown"}:
                    logger.debug("Lifespan shutdown event")
                    await self.emit(LifespanShutdownEvent(scope))
                    await send({"type": "lifespan.shutdown.complete"})
                    running = False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self._state_machine.started:
            try:
                await self._state_machine.cycle()
            except Exception as e:
                logger.exception("Error while starting state machine", exc_info=True)
                raise e

        match scope:
            case {"type": "lifespan"}:
                await self.handle_lifespan(scope, receive, send)

            case _:
                try:
                    await self._middleware_stack(scope, receive, Sender(send))
                except Exception as e:
                    logger.exception("Error in middleware stack", exc_info=True)
                    raise e

    async def _500_response(self, scope: Scope, receive: Receive, send: Sender):
        if send.sent:
            return

        await PlainTextResponse("Internal Server Error", status_code=500)(
            scope, receive, send
        )

    def _build_extensions(self, extension_constructors):
        apply(self.add_extension).to(extension_constructors)

    def _build_middleware_stack(self, middleware_constructors) -> ASGIApp:
        def middleware_factory(previous, current) -> ASGIApp:
            return current(previous)

        return reduce(
            middleware_factory,
            middleware_constructors,
            cast(ASGIApp, self._500_response),
        )

    def _setup_repository(self):
        repo = get_repository()
        repo.add_providers(AtProvider())
        repo.set(WordletteApp, self)

    def _add_extension(self, name: str, extension: Extension):
        self._extensions[name] = extension
        get_repository().set(type(extension), extension)
        if isinstance(extension, Observer):
            extension.observe(self)

    def _set_settings_defaults(self, settings: dict[str, Any]) -> dict[str, Any]:
        settings.setdefault("settings-filename", "settings.wordlette")
        settings.setdefault("working-directory", Path.cwd())
        return settings


class AppSetting(AtAnnotation):
    def __init__(self, key: str, default: Any = Null()):
        self.key = key
        self.default = default

    @inject
    def strategy(self, *_, app: WordletteApp = dependency()):
        match self.default:
            case Null():
                return lambda: app.settings[self.key]

            case _:
                return partial(app.settings.get, self.key, self.default)
