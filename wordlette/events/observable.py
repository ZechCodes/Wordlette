import asyncio
from typing import Type, Generator, TypeVar
from weakref import WeakSet

from wordlette.events.dispatch import Callback, Listener, EventDispatch
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event
from wordlette.utils.contextual_methods import contextual_method

T = TypeVar("T")


class Observable(Dispatchable):
    """An object that can emit events."""

    __instances__: WeakSet["Observable"]
    __children__: WeakSet["Type[Observable]"]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__event_dispatch__ = EventDispatch()
        cls.__children__ = WeakSet()
        cls.__instances__ = WeakSet()

        for parent in cls._get_dispatchable_bases():
            parent.__children__.add(cls)

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        cls.__instances__.add(instance)
        return instance

    @contextual_method
    def listen(obj, event: Type[Event], callback: Callback) -> Listener:
        """Adds a listener to the observable. When called as a class method this will register an event listener that
        listens for events emitted from any instance."""
        return obj.__event_dispatch__.listen(event, callback)

    @contextual_method
    def after(obj, event: Type[Event], callback: Callback) -> Listener:
        """Adds a listener to the observable that is called after the standard listeners run."""
        return obj.__event_dispatch__.after(event, callback)

    @contextual_method
    def before(obj, event: Type[Event], callback: Callback) -> Listener:
        """Adds a listener to the observable that is called before the standard listeners run."""
        return obj.__event_dispatch__.before(event, callback)

    @contextual_method
    async def emit(self, event: Event):
        """Emits an event to all listeners on the instances and propagates up through the superclasses."""
        await self.__event_dispatch__.emit(event)
        await type(self).__event_dispatch__.emit(event)
        await self._emit(self._get_dispatchable_supers(), event)

    @emit.classmethod
    async def emit(cls, event: Event):
        """Emits an event to all instances of the type, all child classes and their instances, and all super types."""
        await cls._emit_instances(event)
        await cls._emit_propagate_children(event)
        await cls._emit(cls._get_dispatchable_supers(), event)

    @contextual_method
    def stop(obj, event: Type[Event], callback: Callback):
        """Removes a listener from the observable."""
        obj.__event_dispatch__.stop(event, callback)

    @contextual_method
    def stop_after(obj, event: Type[Event], callback: Callback):
        """Removes a listener from the observable that is called after the standard listeners run."""
        obj.__event_dispatch__.stop_after(event, callback)

    @contextual_method
    def stop_before(obj, event: Type[Event], callback: Callback):
        """Removes a listener from the observable that is called before the standard listeners run."""
        obj.__event_dispatch__.stop_before(event, callback)

    @staticmethod
    def _emit(objs, event: Event):
        return asyncio.gather(*(obj.__event_dispatch__.emit(event) for obj in objs))

    @classmethod
    async def _emit_instances(cls, event: Event):
        await cls._emit(cls.__instances__, event)
        await asyncio.gather(
            *(child._emit_instances(event) for child in cls.__children__)
        )

    @classmethod
    async def _emit_propagate_children(cls, event):
        if cls.__children__:
            await asyncio.gather(
                *(child._emit_propagate_children(event) for child in cls.__children__)
            )

        await cls.__event_dispatch__.emit(event)

    @classmethod
    def _get_dispatchable_supers(
        cls, *, skip_self: bool = False
    ) -> Generator[Type[Dispatchable], None, None]:
        return cls._get_dispatchable_objects(cls.__mro__[1:], "__event_dispatch__")

    @classmethod
    def _get_dispatchable_bases(cls) -> "Generator[Type[Observable], None, None]":
        return cls._get_dispatchable_objects(cls.__bases__, "__children__")

    @staticmethod
    def _get_dispatchable_objects(objects, attr: str) -> Generator[Type[T], None, None]:
        return (obj for obj in objects if hasattr(obj, attr))
