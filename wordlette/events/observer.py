from types import MethodType
from typing import Type

from wordlette.events import Observable
from wordlette.events.dispatch import Callback
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event


def _unwrap(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    return func


def _get_first_arg_type(func):
    if not hasattr(func, "__annotations__"):
        return None

    if isinstance(func, MethodType):
        return None

    annotations = list(func.__annotations__.values())
    if len(annotations) < 1:
        return None

    return annotations[0]


class Observer(Dispatchable):
    __event_listeners__: dict[Type[Event], Callback]

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        for event_type, listener in cls.__event_listeners__.items():
            instance.__event_dispatch__.listen(
                event_type, MethodType(listener, instance)
            )

        return instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__event_listeners__ = {}
        for name in dir(cls):
            if not name.startswith("_"):
                func = getattr(cls, name)
                arg_type = _get_first_arg_type(_unwrap(func))
                if arg_type and issubclass(arg_type, Event):
                    cls.__event_listeners__[arg_type] = func

    def observe(self, observable: Observable):
        observable.__event_dispatch__.observe(self.__event_dispatch__.emit)
