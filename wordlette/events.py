import asyncio
import inspect
from collections import defaultdict
from types import MethodType
from typing import (
    Callable,
    Type,
    Awaitable,
    TypeAlias,
    Any,
    cast,
    Concatenate,
    ParamSpec,
    TypeVar,
    Generic,
)
from weakref import WeakMethod, ref as WeakRef

from bevy import inject, dependency, get_repository

from wordlette.options import Option

Callback: TypeAlias = Callable[["Event"], Awaitable[None]]
P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


class ClassOrInstanceMethod(Generic[P, R, T]):
    def __init__(self, method: Callable[Concatenate[T, P], R]):
        self.method = method

    def __get__(self, instance: T | None, owner: Type[T]) -> Callable[P, R]:
        return MethodType(self.method, instance or owner)


class Event:
    def __hash__(self):
        return hash(self.__dict__)


class Listener:
    def __init__(
        self, callback: Callback, event_type: Type[Event], event_manager: "EventManager"
    ):
        super().__init__()

        self.callback = self._create_weak_reference(callback)
        self.event_manager = event_manager
        self.event_type = event_type

    def __call__(self, *args, **kwargs):
        return self.callback()(*args, **kwargs)

    def __hash__(self):
        return hash(self.callback)

    def __eq__(self, other):
        match other:
            case Listener():
                return self.callback == other.callback

            case _:
                return self.callback == other

    def stop(self):
        self.event_manager.remove(self.event_type, self.callback)

    def _create_weak_reference(self, callback):
        match callback:
            case MethodType():
                ref_constructor = WeakMethod

            case _:
                ref_constructor = WeakRef

        return ref_constructor(callback, self._on_destroyed)

    def _on_destroyed(self, _):
        self.stop()


class EventManager:
    def __init__(self, parent: "EventManager | None" = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent or NullEventManager.create()
        self._observers: dict[Type[Event], set[Listener]] = defaultdict(set)

    def emit(self, event: Event) -> Awaitable[list[Any]]:
        return asyncio.gather(
            *(observer(event) for observer in self._observers[type(event)]),
            self._parent.emit(event),
        )

    def listen(self, event: Type[Event], observer: Callback) -> Listener:
        listener = Listener(observer, event, self)
        self._observers[event].add(listener)
        return listener

    def remove(self, event: Type[Event], observer: Callback):
        if event in self._observers:
            self._observers[event].remove(cast(Listener, observer))


class NullEventManager(EventManager):
    async def emit(self, event: Event) -> list[Any]:
        return []

    def listen(self, event: Type[Event], observer: Callback) -> Listener:
        return Listener(observer, event, self)

    def remove(self, event: Type[Event], observer: Callback):
        pass

    @classmethod
    def create(cls):
        return cls.__new__(cls)


class Observable:
    _event_manager: EventManager

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._event_manager = EventManager(
            get_repository().find(EventManager).value_or(None)
        )

    @inject
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_manager = EventManager(type(self)._event_manager)

    @ClassOrInstanceMethod
    def emit(obj, event: Event) -> Awaitable[list[Any]]:
        return obj._event_manager.emit(event)

    @ClassOrInstanceMethod
    def listen(obj, event: Type[Event], observer: Callback) -> Listener:
        return obj._event_manager.listen(event, observer)

    @ClassOrInstanceMethod
    def remove(obj, event: Type[Event], observer: Callback):
        obj._event_manager.remove(event, observer)


class Observer:
    _observers: dict[Type[Event], set[Callback]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._find_observers()

    @inject
    def __init__(self, *_, event_manager: EventManager = dependency(), **__):
        super().__init__()
        if not hasattr(self, "_observers"):
            self._find_observers()

        for event_type, observers in self._observers.items():
            for observer in observers:
                event_manager.listen(event_type, getattr(self, observer.__name__))

    @classmethod
    def _find_observers(cls):
        cls._observers = defaultdict(set)
        for function in cls._get_functions():
            match cls.get_handler_type(function):
                case Option.Value(type() as et) if issubclass(et, Event):
                    cls._observers[et].add(function)

    @classmethod
    def _get_functions(cls):
        for name, attr in vars(cls).items():
            if (
                callable(attr)
                and not isinstance(attr, MethodType)
                and not name.startswith("_")
            ):
                yield attr

    @staticmethod
    def get_handler_type(function):
        arg_spec = inspect.getfullargspec(function)
        arg_type = (
            arg_spec.annotations.get(arg_spec.args[1])
            if len(arg_spec.args) > 1
            else None
        )
        return Option.Value(arg_type) if arg_type else Option.Null()
