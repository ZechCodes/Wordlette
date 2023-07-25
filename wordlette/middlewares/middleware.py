from functools import partial
from types import MethodType
from typing import Callable, Awaitable

from starlette.types import Scope, Send

from wordlette.requests import Request


class Middleware:
    def __init__(self, call_next: Callable[[Scope, Request, Send], Awaitable[None]]):
        super().__init__()
        self.call_next = call_next

    async def next(self):
        """Calls the next middleware in the stack. A context aware method is injected at runtime that can correctly call
        the next middleware."""

    async def run(self, scope: Scope, request: Request, send: Send):
        await self.next()

    async def __call__(self, scope: Scope, request: Request, send: Send):
        await call_with_extended_self(
            self.run,
            (scope, request, send),
            {},
            next=partial(self.call_next, scope, request, send),
        )


def call_with_extended_self(method: MethodType, args, kwargs, **extensions):
    self = method.__self__
    extended_type = type("ExtendedType", (self.__class__,), extensions)
    extended_self = object.__new__(extended_type)
    extended_self.__dict__ = self.__dict__
    return method.__func__(extended_self, *args, **kwargs)
