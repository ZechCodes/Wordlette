from wordlette.events.dispatch import Callback, Listener
from wordlette.events.dispatchable import Dispatchable
from wordlette.events.events import Event


class Observable(Dispatchable):
    def on(self, event: Event, callback: Callback) -> Listener:
        return self.__event_dispatch__.listen(event, callback)

    def after(self, event: Event, callback: Callback) -> Listener:
        return self.__event_dispatch__.after(event, callback)

    def before(self, event: Event, callback: Callback) -> Listener:
        return self.__event_dispatch__.before(event, callback)

    async def emit(self, event: Event):
        await self.__event_dispatch__.emit(event)

    def off(self, event: Event, callback: Callback):
        self.__event_dispatch__.stop(event, callback)

    def off_after(self, event: Event, callback: Callback):
        self.__event_dispatch__.stop_after(event, callback)

    def off_before(self, event: Event, callback: Callback):
        self.__event_dispatch__.stop_before(event, callback)
