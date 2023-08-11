from dataclasses import dataclass

from starlette.types import Scope

from wordlette.events import Event


class StartupEvent(Event):
    __event_name__ = "Startup"


@dataclass
class LifespanStartupEvent(Event):
    __event_name__ = "Lifespan.Startup"

    scope: Scope


@dataclass
class LifespanShutdownEvent(Event):
    __event_name__ = "Lifespan.Shutdown"

    scope: Scope
