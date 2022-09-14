from bevy import Context
from types import MethodType
from typing import Awaitable, Callable, TypeVar, ParamSpec, TypeAlias, Type

R = TypeVar("R")
P = ParamSpec("P")

Listener: TypeAlias = Callable[P, Awaitable[R]]


class EventListener:
    def __init__(self, event: str, listen_to: Type, listener: Listener):
        self._event = event
        self._listen_to = listen_to
        self._listener = listener

    def __set_name__(self, owner, name):
        if not hasattr(owner, "__event_listeners__"):
            owner.__event_listeners__ = set()

        owner.__event_listeners__.add(self)

    def __get__(self, instance, owner) -> Listener:
        return self._listener.__get__(instance, owner)

    def register(self, context: Context, instance):
        target = context.find(self._listen_to)
        if target:
            target.on(self._event, MethodType(self._listener, instance))
