class Event:
    __event_count__: int

    def __init_subclass__(cls, **kwargs):
        cls.__event_count__ = 0

    def __new__(cls, *args, **kwargs):
        event_id, cls.__event_count__ = cls.__event_count__, cls.__event_count__ + 1
        instance = super().__new__(cls)
        instance.__event_count__ = event_id
        return instance

    def __repr__(self):
        return f"<{Event.__name__}:{self.__class__.__name__} {self.__event_count__}>"
