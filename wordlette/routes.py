import inspect
from types import MethodType, UnionType
from typing import (
    Type,
    Callable,
    ParamSpec,
    TypeVar,
    Generic,
    Awaitable,
    get_args,
    Any,
)

from starlette.responses import Response
from starlette.types import Scope, Receive, Send

from wordlette.requests import Request

P = ParamSpec("P")
RequestType = TypeVar("RequestType", bound=Request)
ExceptionType = TypeVar("ExceptionType", bound=Exception)


class Route(Generic[RequestType]):
    request_handlers: dict[
        Type[RequestType], Callable[[Any, RequestType], Awaitable[Response]]
    ]
    error_handlers: dict[
        Type[ExceptionType], Callable[[Any, ExceptionType], Awaitable[Response]]
    ]

    def __init_subclass__(cls, **kwargs):
        cls.request_handlers = {}
        cls.error_handlers = {}
        for function in cls._get_functions():
            annotations = inspect.get_annotations(function)
            handler_type = annotations.popitem()[1] if annotations else None
            match handler_type:
                case type() if issubclass(handler_type, (Request, Exception)):
                    cls._register_handlers(function, handler_type)

                case UnionType():
                    cls._register_handlers(function, *get_args(handler_type))

    async def __call__(self, scope, receive, send):
        try:
            await self._handle(scope, receive, send)

        except Exception as error:
            await self._handle_error(error, scope, receive, send)

    async def _handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request.factory(scope)
        if type(request) not in self.request_handlers:
            raise Exception(
                f"Request type {type(request)} not handled by {self.__class__.__qualname__}"
            )

        response = await self.request_handlers[type(request)](self, request)
        await response(scope, receive, send)

    async def _handle_error(
        self,
        exception: Exception,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        handler = self._find_error_handler(type(exception))
        if not handler:
            raise Exception(
                f"Exception type {type(exception)} not handled by {self.__class__.__qualname__}"
            ) from exception

        response = await handler(self, exception)
        await response(scope, receive, send)

    def _find_error_handler(self, exception_type: Type[Exception]):
        for error_type, handler in self.error_handlers.items():
            if exception_type is error_type or issubclass(exception_type, error_type):
                return handler

    @classmethod
    def _get_functions(cls):
        for name, attr in vars(cls).items():
            if (
                callable(attr)
                and not isinstance(attr, MethodType)
                and not name.startswith("_")
            ):
                yield attr

    @classmethod
    def _register_handlers(cls, function, *handler_types):
        if all(issubclass(handler, Request) for handler in handler_types):
            cls._add_handlers(function, handler_types, cls.request_handlers)

        elif all(issubclass(handler, Exception) for handler in handler_types):
            cls._add_handlers(function, handler_types, cls.error_handlers)

    @classmethod
    def _add_handlers(cls, function, handler_types, container):
        for handler_type in handler_types:
            container[handler_type] = function
