class EventMCS(type):
    def __repr__(self):
        return f"<class Event:{self.__name__}>"


class Event(metaclass=EventMCS):
    __event_count__: int
    __event_name__: str

    def __init_subclass__(cls, **kwargs):
        cls.__event_count__ = 0
        if not hasattr(cls, "__event_name__"):
            cls.__event_name__ = cls.__name__

    def __new__(cls, *args, **kwargs):
        event_id, cls.__event_count__ = cls.__event_count__, cls.__event_count__ + 1
        instance = super().__new__(cls)
        instance.__event_count__ = event_id
        return instance

    def __repr__(self):
        return f"<Event:{self.__event_name__} {self.__event_count__}>"
