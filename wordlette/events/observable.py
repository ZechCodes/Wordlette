from wordlette.events.dispatch import Callback, Listener
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event


class Observable(Dispatchable):
    """An object that can emit events."""

    def listen(self, event: Event, callback: Callback) -> Listener:
        """Adds a listener to the observable."""
        return self.__event_dispatch__.listen(event, callback)

    def after(self, event: Event, callback: Callback) -> Listener:
        """Adds a listener to the observable that is called after the standard listeners run."""
        return self.__event_dispatch__.after(event, callback)

    def before(self, event: Event, callback: Callback) -> Listener:
        """Adds a listener to the observable that is called before the standard listeners run."""
        return self.__event_dispatch__.before(event, callback)

    async def emit(self, event: Event):
        """Emits an event to all listeners."""
        await self.__event_dispatch__.emit(event)

    def stop(self, event: Event, callback: Callback):
        """Removes a listener from the observable."""
        self.__event_dispatch__.stop(event, callback)

    def stop_after(self, event: Event, callback: Callback):
        """Removes a listener from the observable that is called after the standard listeners run."""
        self.__event_dispatch__.stop_after(event, callback)

    def stop_before(self, event: Event, callback: Callback):
        """Removes a listener from the observable that is called before the standard listeners run."""
        self.__event_dispatch__.stop_before(event, callback)
