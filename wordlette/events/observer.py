from types import MethodType
from typing import Type, get_origin, get_args, Union, Any

from wordlette.events import Observable
from wordlette.events.dispatch import Callback
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event


def _unwrap(func):
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__

    return func


def _get_first_arg_types(func) -> tuple[Type[Any], ...]:
    if not hasattr(func, "__annotations__"):
        return ()

    if isinstance(func, MethodType):
        return ()

    annotations = list(func.__annotations__.values())
    if len(annotations) < 1:
        return ()

    if get_origin(annotations[0]) is Union:
        return get_args(annotations[0])

    return (annotations[0],)


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
                arg_types = _get_first_arg_types(_unwrap(func))
                for arg_type in arg_types:
                    if isinstance(arg_type, type) and issubclass(arg_type, Event):
                        cls.__event_listeners__[arg_type] = func

    def observe(self, observable: Observable | Type[Observable]):
        observable.__event_dispatch__.propagate_to(self.__event_dispatch__.emit)
