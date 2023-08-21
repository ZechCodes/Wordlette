from inspect import isawaitable
from typing import TypeVar, Awaitable

R = TypeVar("R")


async def maybe_awaitable(r: R | Awaitable[R]):
    if isawaitable(r):
        return await r

    return r
