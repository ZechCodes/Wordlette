from collections import defaultdict

from bevy import Bevy
from typing import Awaitable, Callable, TypeVar, ParamSpec, TypeAlias

from wordlette.utilities.class_instance_dispatch import ClassOrInstanceDispatch
from .listener import EventListener

R = TypeVar("R")
P = ParamSpec("P")

Listener: TypeAlias = Callable[P, Awaitable[R]]


class Eventable(Bevy):
    __event_listeners__: set[EventListener]

    def __init__(self):
        self._register_listeners()

    async def dispatch(self, event: str, *payload_args, **payload_kwargs):
        for listener in self._listeners.get(event, set()):
            await listener(*payload_args, **payload_kwargs)

    @ClassOrInstanceDispatch
    @classmethod
    def on(cls, event: str) -> Callable[[Listener], EventListener]:
        def register(func: Listener) -> EventListener:
            return EventListener(event, cls, func)

        return register

    @on.add_method
    def on(self, event: str, listener: Listener):
        self._listeners[event].add(listener)

    def _register_listeners(self):
        self._listeners: dict[str, set[Listener]] = defaultdict(set)
        for listener in getattr(self, "__event_listeners__", set()):
            listener.register(self.bevy, self)
