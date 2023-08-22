from typing import TypeVar, Generic, Callable

T = TypeVar("T")


class Pipeline(Generic[T]):
    def __init__(self, *callables: Callable[[T], T]):
        self.callables = list(callables)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def run(self, initial_value: T) -> T:
        value = initial_value
        for callable_ in self.callables:
            value = callable_(value)

        return value

    @staticmethod
    def no_params(func: Callable[[], T], *_) -> Callable[[T], T]:
        return lambda _: func()

    @staticmethod
    def with_params(
        func: Callable[[T], T], *args, ignore_value: bool = False, **kwargs
    ) -> Callable[[T], T]:
        def caller(value: T) -> T:
            _args = args if ignore_value else (value, *args)
            return func(*_args, **kwargs)

        return caller
