from typing import Any, Iterable


class Apply:
    def __init__(self, *callables):
        self.callables = callables

    def to(self, *iterables: Iterable[Any]):
        for args in zip(*iterables):
            for callable_ in self.callables:
                callable_(*args)


def apply(*callables) -> Apply:
    return Apply(*callables)
