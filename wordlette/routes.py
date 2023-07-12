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


class ExceptionHandlerContext:
    """When an exception occurs in a route, the exception handler context finds a matching handler on the route. If no
    handler is found the exception will be allowed to propagate. Calling the context object after it has found a handler
    runs the handler and its response, sending the response to the client."""

    path: str  # The path that the route should be mounted at.

    def __init__(self, route: "Route"):
        self.route = route
        self.exception = None
        self.handler = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.handler = self._find_error_handler(exc_type)
        if self.handler:
            self.exception = exc_type(exc_val)
            self.exception.with_traceback(exc_tb)
            return True

    def __bool__(self):
        return self.exception is not None

    async def __call__(self, scope, receive, send):
        response = await self.handler(self.route, self.exception)
        await response(scope, receive, send)

    def _find_error_handler(self, exception_type: Type[Exception]):
        for error_type, handler in self.route.error_handlers.items():
            if exception_type is error_type or issubclass(exception_type, error_type):
                return handler


class Route(Generic[RequestType]):
    """The route type handles all the magic that allows routes to be defined without any decorator boilerplate. It
    provides the instrumentation necessary for simple request handling by method type using type annotations. It also
    provides a simple exception handling mechanism using the same approach.

    To declare a request handler create an async method with whatever name you think is appropriate. Then all you have
    to do is set the type annotion of the first parameter to the request type your handler should handle. For example:
    ```python
    class MyRoute(Route):
        async def index(self, request: Request.Get):
            return PlainTextResponse("Hello World!")
    ```
    Handling errors is just as simple and follows the exact same process. The exception type will match all exceptions
    that pass a subclass check, so it should function the same as an equivalent try/except. For example:
    ```python
    class MyRoute(Route):
        ...
        async def handle_exception(self, error: Exception):
            return PlainTextResponse("An error occurred!")
    ```
    """

    request_handlers: dict[
        Type[RequestType], Callable[[Any, RequestType], Awaitable[Response]]
    ]
    error_handlers: dict[
        Type[ExceptionType], Callable[[Any, ExceptionType], Awaitable[Response]]
    ]

    def __init_subclass__(cls, **kwargs):
        """Scan the subclass for request and error handlers."""
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
        """Handle a request, calling the appropriate handler function and capturing any handleable exceptions."""
        async with ExceptionHandlerContext(self) as error_handler:
            await self._handle(scope, receive, send)

        if error_handler:
            await error_handler(scope, receive, send)

    async def _handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request.factory(scope)
        if type(request) not in self.request_handlers:
            raise Exception(
                f"Request type {type(request)} not handled by {self.__class__.__qualname__}"
            )

        response = await self.request_handlers[type(request)](self, request)
        await response(scope, receive, send)

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
