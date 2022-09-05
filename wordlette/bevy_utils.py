from bevy import Context
from typing import TypeVar

from wordlette.exceptions import WordletteNotBoundToABevyContextError

T = TypeVar("T")


class UnboundBevyContext(Context):
    def __get__(self, instance, __):
        raise WordletteNotBoundToABevyContextError(
            f"{instance!r} is not bound to a Bevy context"
        )


def bind_proxy(context: Context, instance: T) -> T:
    return BindProxy(context, instance)


class BindProxy:
    __setter = object.__setattr__

    def __init__(self, context: Context, obj):
        self.bevy = context
        self.__obj = obj
        self.__setter = self.__setattr

    def __getattr__(self, item):
        value = getattr(self.__obj, item)
        if hasattr(value, "__func__"):
            value = value.__func__.__get__(self, type(self.__obj))

        return value

    def __setattr__(self, key, value):
        self.__setter(key, value)

    def __setattr(self, key, value):
        if key in dir(self):
            super().__setattr__(key, value)
            return

        setattr(self.__obj, key, value)
