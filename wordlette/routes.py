import inspect
from collections import ChainMap
from types import MethodType, UnionType
from typing import (
    Type,
    ParamSpec,
    TypeVar,
    Generic,
    Any,
    cast,
    MutableMapping,
    get_args,
)

from starlette.types import Scope, Receive, Send

from wordlette.object_proxy_map import ObjectProxyMap
from wordlette.options import Option
from wordlette.pipeline import Pipeline
from wordlette.requests import Request

P = ParamSpec("P")
RequestType = TypeVar("RequestType", bound=Request)
ExceptionType = TypeVar("ExceptionType", bound=Exception)


class MissingRoutePath(Exception):
    """Raised when a route is missing a path."""


class NoRouteHandlersFound(Exception):
    """Raised when a route has no registered method handlers."""


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
        for error_type, handler in self.route.__route_meta__["error_handlers"].items():
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

    class RouteMeta:
        abstract: True
        registry: "set[Type[Route]]" = set()
        __route__ = None

    __route_meta__: ChainMap[str, Any] = ChainMap(
        cast(MutableMapping, ObjectProxyMap(RouteMeta))
    )
    methods: tuple[str]
    name: str

    path: str

    def __init_subclass__(cls, **kwargs):
        """Setup the route class building the route meta, scanning for request & error handlers, and ensuring that
        concrete routes have a path and route handlers."""
        meta = cls._build_route_meta(kwargs)

        meta.setdefault("request_handlers", {})
        meta.setdefault("error_handlers", {})
        cls._find_and_register_handlers()

        if not hasattr(cls, "name"):
            cls.name = cls.__qualname__.casefold()

        if not cls.__route_meta__["abstract"]:
            cls.__route_meta__["registry"].add(cls)

            cls.methods = cast(
                tuple[str],
                tuple(
                    handler.name for handler in cls.__route_meta__["request_handlers"]
                ),
            )
            if not hasattr(cls, "path"):
                raise MissingRoutePath(
                    f"Route subclass {cls.__qualname__} is missing a path attribute."
                )

            if not cls.methods:
                raise NoRouteHandlersFound(
                    f"Route subclass {cls.__qualname__} has no request handlers."
                )

    async def __call__(self, scope, receive, send):
        """Handle a request, calling the appropriate handler function and capturing any handleable exceptions."""
        async with ExceptionHandlerContext(self) as error_handler:
            await self._handle(scope, receive, send)

        if error_handler:
            await error_handler(scope, receive, send)

    async def _handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request.factory(scope)
        if type(request) not in self.__route_meta__["request_handlers"]:
            raise Exception(
                f"Request type {type(request)} not handled by {self.__class__.__qualname__}"
            )

        response = await self.__route_meta__["request_handlers"][type(request)](
            self, request
        )
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
            cls._add_handlers(
                function, handler_types, cls.__route_meta__["request_handlers"]
            )

        elif all(issubclass(handler, Exception) for handler in handler_types):
            cls._add_handlers(
                function, handler_types, cls.__route_meta__["error_handlers"]
            )

    @classmethod
    def _add_handlers(cls, function, handler_types, container):
        for handler_type in handler_types:
            container[handler_type] = function

    @classmethod
    def get_handler_type(cls, function):
        arg_spec = inspect.getfullargspec(cls._unwrap(function))
        arg_type = (
            arg_spec.annotations.get(arg_spec.args[1])
            if len(arg_spec.args) > 1
            else None
        )
        return Option.Value(arg_type) if arg_type else Option.Null()

    @staticmethod
    def _unwrap(function):
        while hasattr(function, "__wrapped__"):
            function = function.__wrapped__

        return function

    @classmethod
    def _build_route_meta(cls, meta_params: dict[str, Any]) -> ChainMap[str, Any]:
        pipeline = Pipeline[ChainMap[str, Any]](
            cls._setup_meta_route_object,
            Pipeline.with_params(cls._load_meta_route_params, meta_params),
            ChainMap.new_child,
        )
        cls.__route_meta__ = pipeline.run(cls.__route_meta__)
        return cls.__route_meta__

    @classmethod
    def _setup_meta_route_object(
        cls, route_meta: ChainMap[str, Any]
    ) -> ChainMap[str, Any]:
        if not hasattr(cls.RouteMeta, "__route__"):
            cls.RouteMeta.__route__ = cls

        elif cls.RouteMeta.__route__ is not cls:
            cls.RouteMeta = type("RouteMeta", (), {"__route__": cls})

        if not hasattr(cls.RouteMeta, "abstract"):
            cls.RouteMeta.abstract = False

        return route_meta.new_child(cast(MutableMapping, ObjectProxyMap(cls.RouteMeta)))

    @classmethod
    def _load_meta_route_params(
        cls, route_meta: ChainMap[str, Any], meta_params: dict[str, Any]
    ) -> ChainMap[str, Any]:
        return route_meta.new_child(meta_params)

    @classmethod
    def _find_and_register_handlers(cls):
        for function in cls._get_functions():
            handler_type = cls.get_handler_type(function)
            match handler_type:
                case Option.Value(type() as ht) if issubclass(ht, (Request, Exception)):
                    cls._register_handlers(function, ht)

                case Option.Value(UnionType() as ht):
                    cls._register_handlers(function, *get_args(ht))
