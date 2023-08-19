from typing import Any, Iterable


def apply(iterable: Iterable[Any], *callables):
    for arg in iterable:
        for callable_ in callables:
            callable_(arg)


def star_apply(iterable: Iterable[Any], *callables):
    def splat(callable_):
        def wrapper(args):
            callable_(*args)

        return wrapper

    return apply(iterable, *map(splat, callables))
