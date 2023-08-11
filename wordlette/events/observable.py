from typing import Type, Generator

from wordlette.contextual_methods import contextual_method
from wordlette.events.dispatch import Callback, Listener, EventDispatch
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event


class Observable(Dispatchable):
    """An object that can emit events."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__event_dispatch__ = EventDispatch()
        for parent in cls._get_dispatchable_bases():
            parent.__event_dispatch__.observe(cls.emit)

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        cls.__event_dispatch__.observe(instance.__event_dispatch__.emit)
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
        """Emits an event to all listeners. This will propagate the event to all listeners registered on the instance
        and on the type."""
        await self.__event_dispatch__.emit(event)
        for parent in self._get_dispatchable_supers():
            await parent.__event_dispatch__.emit(event)

    @emit.classmethod
    async def emit(cls, event: Event):
        """Emits an event to all listeners registered on the type and all instances."""
        await cls.__event_dispatch__.emit(event)

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

    @classmethod
    def _get_dispatchable_supers(cls) -> Generator[Type[Dispatchable], None, None]:
        return cls._get_dispatchable_objects(cls.__mro__)

    @classmethod
    def _get_dispatchable_bases(cls) -> Generator[Type[Dispatchable], None, None]:
        return cls._get_dispatchable_objects(cls.__bases__)

    @staticmethod
    def _get_dispatchable_objects(objects) -> Generator[Type[Dispatchable], None, None]:
        return (obj for obj in objects if hasattr(obj, "__event_dispatch__"))
