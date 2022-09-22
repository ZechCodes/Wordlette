from html import escape

import logging
import uvicorn
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.types import Receive, Scope, Send
from typing import Any, Callable, Iterator, Type, TypeAlias

from bevy import Context, bevy_method, Inject
from wordlette.app.states import BaseAppState, Starting
from wordlette.config.provider import ConfigProvider
from wordlette.exceptions import WordletteException, WordletteNoStarletteAppFound
from wordlette.extensions.auto_loader import ExtensionInfo
from wordlette.extensions.extensions import AppExtension, Extension
from wordlette.extensions.plugins import Plugin
from wordlette.logger import LoggingProvider, Logging
from wordlette.policies.provider import PolicyProvider
from wordlette.settings import Settings
from wordlette.state_machine import StateMachine
from wordlette.state_machine.machine import StateChangeEvent
from wordlette.templates import TemplateEngine
from .base_app import BaseApp

StateMachineConstructor: TypeAlias = (
    Type[StateMachine] | Callable[[BaseApp], StateMachine] | Callable[[], StateMachine]
)


class ResponseContext:
    def __init__(self, wordlette: BaseApp, scope: Scope, receive: Receive, send: Send):
        self.scope = scope
        self.receive = receive
        self.send = send
        self.wordlette = wordlette
        self._app = None

    async def __aenter__(self):
        return self

    @property
    def app(self) -> Starlette | None:
        return self.wordlette.app if self.wordlette.context else None

    @app.setter
    def app(self, app: Starlette):
        self._app = app

    def _build_response_error_message(self, content: str, *debug: Any):
        message = f"<p>{content}</p>"
        if self.wordlette.bevy.get(Settings).get("dev", False):
            state = self.wordlette.state_machine.state
            message += (
                f"<h3>Current Context</h4>"
                f"<pre>"
                f"{escape(f'<App:{self.app!r}>')}\n"
                f"{escape(repr(state))}\n"
                + (
                    "\n".join(
                        escape(f"<{type(item).__name__}:{item}>") for item in debug
                    )
                )
                + "</pre>"
            )

        return message

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            match exc_val:
                case WordletteException():
                    message = self._build_response_error_message(
                        exc_val.args[0], exc_val
                    )
                case _:
                    message = self._build_response_error_message(
                        "Something unexpected has happened and Wordlette cannot recover. Please have an admin check "
                        "the system logs for more information.",
                        exc_val,
                    )

            self.app = app = HTMLResponse(
                f"<h1>Wordlette Enountered An Error</h1>{message}",
                status_code=500,
            )

        elif not self.app:
            message = self._build_response_error_message(
                "Wordlette could not find an application to build a response with."
            )
            self.app = self.app = app = HTMLResponse(
                f"<h1>Wordlette Enountered A Problem</h1>{message}",
                status_code=500,
            )

        await self.app(self.scope, self.receive, self.send)


class App(BaseApp):
    def __init__(self, starting_state: Type[BaseAppState] = Starting):
        self.extensions = set()
        self.template_engine = self.bevy.create(
            TemplateEngine, "SITE", [Path("themes").resolve() / "default"], cache=True
        )
        self._state_machine = self.bevy.create(StateMachine, cache=True)
        self._starting_state = starting_state

        super().__init__()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async with ResponseContext(self, scope, receive, send):
            if not self.state_machine.started:
                await self._start()

            logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

            if not self.app:
                if self.state_machine.last_exception:
                    raise self.state_machine.last_exception

                raise WordletteNoStarletteAppFound(
                    f"The application has not loaded any page routes that Wordlette can use."
                )

    @classmethod
    def start(cls, host: str, port: int, extensions_modules: Iterator[str]):
        context = Context.factory()
        context.add_provider(ConfigProvider)
        context.add_provider(PolicyProvider)
        context.add_provider(LoggingProvider)
        app = context.create(cls, cache=True)
        uvicorn.run(app, host=host, port=port)

    def load_app_extension(self, extension_info: ExtensionInfo):
        self._load_extension(extension_info, AppExtension)

    def load_extension(self, extension_info: ExtensionInfo):
        self._load_extension(extension_info, Extension)

    def _load_extension(
        self, extension_info: ExtensionInfo, extension_type: Type[Extension]
    ):
        context = self.app_context.branch()
        context.create(
            TemplateEngine,
            extension_info.name,
            [extension_info.path / "templates"] if extension_info.path.is_dir() else [],
            self.template_engine,
            cache=True,
        )
        logger = self.app_context.create(Logging[extension_info.name], cache=False)
        context.add(
            logger,
            use_as=Logging,
        )
        extension: Extension = context.create(
            extension_type, extension_info.import_path, cache=True
        )
        self.extensions.add(extension)

        logger.info(f"{extension_type.__name__} Loading: {extension.name}")
        extension.load_plugins(
            constructor for constructor in extension_info.found_classes[Plugin]
        )
        logger.info(f"{extension_type.__name__} Loaded: {extension.name}")

    @StateMachine.on("transitioned-to-state")
    @bevy_method
    async def _log_state_transition_to(
        self, event: StateChangeEvent, logger: Logging = Inject
    ):
        logger.info(f"Transitioning {event.old_state} to {event.new_state}")

    @StateMachine.on("entered-state")
    @bevy_method
    async def _log_state_entered(
        self, event: StateChangeEvent, logger: Logging = Inject
    ):
        logger.info(f"Entered {event.new_state} from {event.old_state}")

    @property
    def app(self) -> Starlette | None:
        return self.context.find(Starlette)

    @property
    def app_context(self) -> Context:
        return self.bevy

    @property
    def context(self) -> Context:
        return self.state_machine.state.context

    @property
    def router(self) -> Starlette | None:
        return self.context.find(Starlette)

    @property
    def state_machine(self) -> StateMachine[BaseAppState]:
        return self._state_machine

    @bevy_method
    async def _start(self, logger: Logging = Inject):
        try:
            await self.state_machine.start(self._starting_state)
        except Exception as exception:
            logger.exception("ERROR ENCOUNTERED")
