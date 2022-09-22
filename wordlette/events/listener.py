from functools import update_wrapper
from types import MethodType
from typing import Awaitable, Callable, ParamSpec, Type, TypeAlias, TypeVar

from bevy import bevy_method, Context


R = TypeVar("R")
P = ParamSpec("P")

Listener: TypeAlias = Callable[P, Awaitable[R]]


class EventListener:
    def __init__(self, listen_to: Type, listener: Listener, **labels):
        self._listen_to = listen_to
        self._listener = listener
        self._labels = labels
        update_wrapper(self, listener)

    def __set_name__(self, owner, name):
        if not hasattr(owner, "__event_listeners__"):
            owner.__event_listeners__ = set()

        owner.__event_listeners__.add(self)

    def __get__(self, instance, owner) -> Listener:
        return self._listener.__get__(instance, owner)

    def register(self, context: Context, instance):
        target = context.find(self._listen_to)
        if target:
            func = self._listener
            if hasattr(instance, "bevy"):
                func = bevy_method(self._listener)

            target.on(MethodType(func, instance), **self._labels)
