from wordlette.app.app_protocol import AppProtocol
from wordlette.state_machine import StateMachine
from wordlette.app.app_state import AppState, StateChangeEvent
from bevy import Bevy, Context, Inject
from wordlette.smart_functions import call
from typing import Callable, Iterator, Type, TypeAlias
from starlette.types import Receive, Scope, Send
from starlette.applications import Starlette
from wordlette.exceptions import WordletteNoStarletteAppFound
import logging
import uvicorn
from wordlette.events import EventManager
from copy import deepcopy


StateMachineConstructor: TypeAlias = (
    Type[StateMachine]
    | Callable[[AppProtocol], StateMachine]
    | Callable[[], StateMachine]
)

logger = logging.getLogger("wordlette")


class App(Bevy):
    events: EventManager = Inject

    def __init__(self, state_machine_constructor: StateMachineConstructor = AppState):
        self.events.listen({"type": "changing-state"}, self._log_state_transition)
        self._state = call(self.bevy.bind(state_machine_constructor), self)

    async def _log_state_transition(self, event: StateChangeEvent):
        logger.info(f"{event.old_state} -> {event.new_state}")

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
        app = cls()
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
