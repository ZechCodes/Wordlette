from dataclasses import dataclass

from starlette.types import Scope

from wordlette.events import Event


@dataclass
class LifespanStartupEvent(Event):
    scope: Scope


@dataclass
class LifespanShutdownEvent(Event):
    scope: Scope
