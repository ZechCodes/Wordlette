from wordlette.events.dispatch import EventDispatch


class Dispatchable:
    __event_dispatch__: EventDispatch

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__event_dispatch__ = EventDispatch()
        return instance
