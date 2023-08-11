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
        self._stop(self)

    def _setup_callback(self, callback) -> ref[Callback]:
        weak_type = WeakMethod if isinstance(callback, MethodType) else ref
        return weak_type(callback, self._when_deleted)

    def _when_deleted(self, _: ref):
        self._stop(self)


class EventDispatch:
    """Dispatches events to listeners by type. All events can also be forwarded to an observer. There is support for
    applying listeners that run before or after the standard event listeners."""

    def __init__(self):
        self.after_listeners: Registry = defaultdict(set)
        self.before_listeners: Registry = defaultdict(set)
        self.listeners: Registry = defaultdict(set)
        self.observers: set[Callback] = set()

    def after(self, event: Type[Event], callback: Callback) -> Listener:
        """Registers an event listener that runs after the standard event listeners."""
        return self._register_listener(
            event, callback, self.after_listeners, self.stop_after
        )

    def before(self, event: Type[Event], callback: Callback) -> Listener:
        """Registers an event listener that runs before the standard event listeners."""
        return self._register_listener(
            event, callback, self.before_listeners, self.stop_before
        )

    async def emit(self, event: Event):
        """Emits an event to all listeners and observers."""
        event_type = type(event)
        listener_registries = (
            self.before_listeners[event_type],
            self.listeners[event_type],
            self.after_listeners[event_type],
            self.observers,
        )
        for listeners in listener_registries:
            await self._run_handlers(listeners, event)

    def listen(self, event: Type[Event], callback: Callback) -> Listener:
        """Registers an event listener."""
        return self._register_listener(event, callback, self.listeners, self.stop)

    def propagate_to(self, callback: Callback):
        """Adds an observer that will receive all events."""
        self.observers.add(callback)

    def stop(self, event: Type[Event], callback: Callback):
        """Stops an event listener."""
        self._stop_listener(event, callback, self.listeners)

    def stop_after(self, event: Type[Event], callback: Callback):
        """Stops an event listener that runs after the standard event listeners."""
        self._stop_listener(event, callback, self.after_listeners)

    def stop_before(self, event: Type[Event], callback: Callback):
        """Stops an event listener that runs before the standard event listeners."""
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
