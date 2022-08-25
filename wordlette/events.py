from typing import Any, Awaitable, Callable, Hashable, ParamSpec, TypeVar
from functools import cache, lru_cache
import asyncio


P = ParamSpec("P")
T = TypeVar("T")

Handler = Callable[P, Awaitable[T]]
Label = dict[str, Hashable]


class Listener:
    def __init__(self, label: Label, handler: Handler):
        self.label = label
        self.handler = handler
        self._hash = None

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        return self.handler(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, Listener):
            return hash(self) == hash(other)

        raise NotImplemented()

    def __hash__(self):
        if not self._hash:
            self._hash = hash((*self.label.items(), self.handler))

        return self._hash

    def matches(self, label: Label) -> bool:
        return self.label.items() <= label.items()


class EventManager:
    def __init__(self):
        self._listeners = set()

    async def dispatch(self, label: Label, *args: P.args, **kwargs: P.kwargs):
        await asyncio.gather(
            *(
                listener(*args, **kwargs)
                for listener in self._listeners
                if listener.matches(label)
            )
        )

    def listen(self, label: Label, handler: Handler):
        self._listeners.add(Listener(label, handler))
