import logging
import uvicorn
from bevy import Bevy, Context, Inject
from copy import deepcopy
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send
from typing import Callable, Iterator, Type, TypeAlias

from wordlette.app.app_protocol import AppProtocol
from wordlette.app.app_state import AppState
from wordlette.events import EventManager
from wordlette.exceptions import WordletteNoStarletteAppFound
from wordlette.extensions.auto_loader import ExtensionInfo
from wordlette.extensions.extensions import AppExtension, Extension
from wordlette.extensions.plugins import Plugin
from wordlette.smart_functions import call
from wordlette.state_machine import StateMachine
from wordlette.state_machine.machine import StateChangeEvent

StateMachineConstructor: TypeAlias = (
    Type[StateMachine]
    | Callable[[AppProtocol], StateMachine]
    | Callable[[], StateMachine]
)

logger = logging.getLogger("wordlette")


class App(Bevy):
    events: EventManager = Inject

    def __init__(self, state_machine_constructor: StateMachineConstructor = AppState):
        self.extensions = set()
        self._state = call(self.bevy.bind(state_machine_constructor), self)
        self.events.listen({"type": "changing-state"}, self._log_state_transition_to)
        self.events.listen({"type": "changed-state"}, self._log_state_entered)

    def load_app_extension(self, extension_info: ExtensionInfo):
        self._load_extension(extension_info, AppExtension)

    def load_extension(self, extension_info: ExtensionInfo):
        self._load_extension(extension_info, Extension)

    def _load_extension(
        self, extension_info: ExtensionInfo, extension_type: Type[Extension]
    ):
        context = self.app_context.branch()
        extension: Extension = context.create(
            extension_type, extension_info.import_path, cache=True
        )
        self.extensions.add(extension)

        logger.info(f"Loading {extension_type.__name__}: {extension.name}")
        extension.load_plugins(
            constructor for constructor in extension_info.found_classes[Plugin]
        )
        logger.info(f"{extension_type.__name__} Loaded: {extension.name}")

    async def _log_state_transition_to(self, event: StateChangeEvent):
        logger.info(f"Transitioning {event.old_state} to {event.new_state}")

    async def _log_state_entered(self, event: StateChangeEvent):
        logger.info(f"Entered {event.new_state} from {event.old_state}")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
        if not self.state.started:
            await self._start()

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
        return self.bevy

    @property
    def context(self) -> Context:
        return self.state.value

    @property
    def state(self) -> StateMachine:
        return self._state

    async def _start(self):
        try:
            await self.state.start(self.state.starting, self)
        except Exception as exception:
            logger.exception("ERROR ENCOUNTERED")

    @classmethod
    def start(cls, host: str, port: int, extensions_modules: Iterator[str]):
        context = Context.factory()
        app = context.create(cls, cache=True)
        uvicorn.run(app, host=host, port=port, log_config=cls._create_logging_config())

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
