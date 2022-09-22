from typing import Awaitable, Callable, ParamSpec, TypeAlias, TypeVar

from bevy import Bevy

from wordlette.labels import LabelCollection
from wordlette.utilities.class_instance_dispatch import ClassOrInstanceDispatch
from .listener import EventListener


R = TypeVar("R")
P = ParamSpec("P")
T = TypeVar("T")

Listener: TypeAlias = Callable[P, Awaitable[R]]


class Eventable(Bevy):
    __event_listeners__: set[EventListener]
    _listeners: LabelCollection[Listener]

    def __init__(self):
        self._register_listeners()

    async def dispatch(self, *payload_args, **labels):
        for listener in self._listeners.get(**labels):
            await listener(*payload_args)

    @ClassOrInstanceDispatch
    @classmethod
    def on(cls, **labels) -> Callable[[Listener], EventListener]:
        def register(func: Listener) -> EventListener:
            return EventListener(cls, func, **labels)

        return register

    @on.add_method
    def on(self, listener: Listener, **labels):
        self._listeners.add(listener, **labels)

    def _register_listeners(self):
        self._listeners = LabelCollection[Listener]()
        for listener in getattr(self, "__event_listeners__", set()):
            listener.register(self.bevy, self)
