import logging
import uvicorn
from bevy import Context
from copy import deepcopy
from pathlib import Path
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send
from typing import Callable, Iterator, Type, TypeAlias

from wordlette.app.states import BaseAppState, Starting
from wordlette.exceptions import WordletteNoStarletteAppFound
from wordlette.extensions.auto_loader import ExtensionInfo
from wordlette.extensions.extensions import AppExtension, Extension
from wordlette.extensions.plugins import Plugin
from wordlette.policies.provider import PolicyProvider
from wordlette.state_machine import StateMachine
from wordlette.state_machine.machine import StateChangeEvent
from wordlette.templates import TemplateEngine
from .base_app import BaseApp

StateMachineConstructor: TypeAlias = (
    Type[StateMachine] | Callable[[BaseApp], StateMachine] | Callable[[], StateMachine]
)

logger = logging.getLogger("wordlette")


class App(BaseApp):
    def __init__(self, starting_state: Type[BaseAppState] = Starting):
        self.extensions = set()
        self.template_engine = self.bevy.create(
            TemplateEngine, "SITE", [Path("themes").resolve() / "default"], cache=True
        )
        self._state_machine = self.bevy.create(StateMachine, cache=True)
        self._starting_state = starting_state

        super().__init__()

    @classmethod
    def start(cls, host: str, port: int, extensions_modules: Iterator[str]):
        context = Context.factory()
        context.add_provider(PolicyProvider)
        app = context.create(cls, cache=True)
        uvicorn.run(app, host=host, port=port, log_config=cls._create_logging_config())

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
            extension_info.path.stem,
            [extension_info.path / "templates"] if extension_info.path.is_dir() else [],
            self.template_engine,
            cache=True,
        )
        extension: Extension = context.create(
            extension_type, extension_info.import_path, cache=True
        )
        self.extensions.add(extension)

        logger.info(f"Loading {extension_type.__name__}: {extension.name}")
        extension.load_plugins(
            constructor for constructor in extension_info.found_classes[Plugin]
        )
        logger.info(f"{extension_type.__name__} Loaded: {extension.name}")

    @StateMachine.on("transitioned-to-state")
    async def _log_state_transition_to(self, event: StateChangeEvent):
        logger.info(f"Transitioning {event.old_state} to {event.new_state}")

    @StateMachine.on("entered-state")
    async def _log_state_entered(self, event: StateChangeEvent):
        logger.info(f"Entered {event.new_state} from {event.old_state}")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
        if not self.state_machine.started:
            await self._start()

        if not self.app:
            raise WordletteNoStarletteAppFound(
                f"Cannot handle {scope['type']=} because the current application state_machine has not added a Starlette app "
                "to the context."
            )

        await self.app(scope, receive, send)

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

    async def _start(self):
        try:
            await self.state_machine.start(self._starting_state)
        except Exception as exception:
            logger.exception("ERROR ENCOUNTERED")

    @staticmethod
    def _create_logging_config():
        log_config = deepcopy(uvicorn.config.LOGGING_CONFIG)

        log_config["formatters"]["default"][
            "fmt"
        ] = f'  UVICORN.{log_config["formatters"]["default"]["fmt"]}'
        log_config["formatters"]["access"][
            "fmt"
        ] = f'   ACCESS.{log_config["formatters"]["access"]["fmt"]}'

        log_config["formatters"]["wordlette"] = {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "WORDLETTE.%(levelprefix)s %(message)s",
            "use_colors": None,
        }
        log_config["handlers"]["wordlette"] = {
            "formatter": "wordlette",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        }
        log_config["loggers"]["wordlette"] = {
            "handlers": ["wordlette"],
            "level": "INFO",
        }
        return log_config
