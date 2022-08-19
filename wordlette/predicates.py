from __future__ import annotations
from typing import Any, Awaitable, Callable, Iterable, ParamSpec, TypeAlias
from inspect import iscoroutinefunction


P = ParamSpec("P")
PredicateFunction: TypeAlias = Callable[P, Awaitable[bool] | bool]


def predicate(*predicates) -> OrPredicate:
    return OrPredicate(*predicates)


async def _call(func: Callable[[...], Any], *args, **kwargs) -> Any:
    result = func(*args, **kwargs)
    if _is_coroutine(func):
        result = await result

    return result


def _is_coroutine(obj) -> bool:
    if iscoroutinefunction(obj):
        return True

    return iscoroutinefunction(getattr(obj, "__call__", None))


class AndPredicate:
    def __init__(self, *predicates: PredicateFunction):
        self._predicates = list(predicates)

    async def __call__(self, *args: P.args, **kwargs: P.kwargs):
        for predicate in self._predicates:
            if not await _call(predicate, *args, **kwargs):
                return False

        return True

    def __and__(self, other):
        self._predicates.append(other)
        return self

    def __or__(self, other):
        return OrPredicate(self, other)

    def __invert__(self):
        return InversePredicate(self)


class OrPredicate(AndPredicate):
    async def __call__(self, *args, **kwargs):
        for predicate in self._predicates:
            if await _call(predicate, *args, **kwargs):
                return True

        return False

    def __and__(self, other):
        return AndPredicate(self, other)

    def __or__(self, other):
        self._predicates.append(other)
        return self


class InversePredicate(AndPredicate):
    async def __call__(self, *args, **kwargs):
        return not await _call(self._predicates[0], *args, **kwargs)

    def __and__(self, other):
        return AndPredicate(self, other)

    def __invert__(self):
        return self._predicates[0]
