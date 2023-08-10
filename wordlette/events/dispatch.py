import asyncio
from collections import defaultdict
from functools import partial
from types import MethodType
from typing import Type, Callable, Awaitable, cast, TypeAlias, Any, Coroutine
from weakref import WeakMethod, ref

from wordlette.events.events import Event

Callback: TypeAlias = "Callable[[Event], Coroutine[Any, Any, None]] | Listener"
Registry: TypeAlias = dict[Type[Event], set[Callback]]
StopCallback: TypeAlias = Callable[[Callback], None]


class Listener:
    def __init__(self, callback: Callback, stop: StopCallback):
        self._callback = self._setup_callback(callback)
        self._stop = stop
        self._hash = hash(self.callback)

    def __call__(self, event: Event) -> Awaitable[None]:
        return self.callback(event)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if callable(other):
            return self._hash == hash(other)

        raise TypeError(
            f"Cannot compare {self.__class__.__name__} to {other.__class__.__name__}"
        )

    @property
    def callback(self) -> Callable[[Event], Awaitable[None]]:
        return self._callback()

    def stop(self):
        self._stop(self.callback)

    def _setup_callback(self, callback) -> ref[Callback]:
        weak_type = WeakMethod if isinstance(callback, MethodType) else ref
        return weak_type(callback, self._when_deleted)

    def _when_deleted(self, _: ref):
        self._stop(self)


class EventDispatch:
    def __init__(self):
        self.after_listeners: Registry = defaultdict(set)
        self.before_listeners: Registry = defaultdict(set)
        self.listeners: Registry = defaultdict(set)
        self.observers: set[Callback] = set()

    def observe(self, callback: Callback):
        self.observers.add(callback)

    def after(self, event: Type[Event], callback: Callback) -> Listener:
        return self._register_listener(
            event, callback, self.after_listeners, self.stop_after
        )

    def before(self, event: Type[Event], callback: Callback) -> Listener:
        return self._register_listener(
            event, callback, self.before_listeners, self.stop_before
        )

    async def emit(self, event: Event):
        for listeners in (self.before_listeners, self.listeners, self.after_listeners):
            await self._run_handlers(listeners[type(event)], event)

        for observer in self.observers:
            await observer(event)

    def listen(self, event: Type[Event], callback: Callback) -> Listener:
        return self._register_listener(event, callback, self.listeners, self.stop)

    def stop(self, event: Type[Event], callback: Callback):
        self._stop_listener(event, callback, self.listeners)

    def stop_after(self, event: Type[Event], callback: Callback):
        self._stop_listener(event, callback, self.after_listeners)

    def stop_before(self, event: Type[Event], callback: Callback):
        self._stop_listener(event, callback, self.before_listeners)

    def _register_listener(
        self,
        event: Type[Event],
        callback: Callback,
        registry: Registry,
        stop: Callable[[Type[Event], Callback], None],
    ) -> Listener:
        listener = Listener(callback, partial(stop, event))
        registry[event].add(listener)
        return listener

    async def _run_handlers(self, listeners: set[Callback], event: Event):
        if not listeners:
            return

        return await asyncio.gather(*(listener(event) for listener in listeners))

    def _stop_listener(
        self, event: Type[Event], callback: Callback, registry: Registry
    ):
        if event not in registry:
            return

        if callback not in registry[event]:
            return

        registry[event].remove(cast(Listener, callback))
