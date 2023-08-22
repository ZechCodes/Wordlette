import inspect
from collections.abc import Set
from types import MethodType, UnionType
from typing import (
    Any,
    Callable,
    Generic,
    Iterator,
    ParamSpec,
    Type,
    TypeVar,
    cast,
    get_args,
)

from starlette.types import Scope, Receive, Send

from wordlette.core.exceptions import MissingRoutePath, NoRouteHandlersFound
from wordlette.requests import Request
from wordlette.routers import Router
from wordlette.routes.exception_contexts import ExceptionHandlerContext
from wordlette.utils.apply import apply
from wordlette.utils.match_types import TypeMatchable
from wordlette.utils.options import Option

P = ParamSpec("P")
RequestType = TypeVar("RequestType", bound=Request)
ExceptionType = TypeVar("ExceptionType", bound=Exception)


class MethodsCollection(Set[Type[Request]]):
    def __init__(self, *methods: Type[Request]):
        self._methods = set(methods)

    @property
    def names(self):
        return [method.name for method in self]

    def __contains__(self, request: Request | Type[Request]) -> bool:
        request_type = type(request) if isinstance(request, Request) else request
        return request_type in self._methods

    def __iter__(self) -> Iterator[Type[Request]]:
        return iter(self._methods)

    def __len__(self) -> int:
        return len(self._methods)

    def __repr__(self):
        return f"<{type(self).__name__} {{{', '.join(sorted(method.name for method in self))}}}>"


class RouteMetadata:
    abstract: bool
    registry: "set[Type[Route]]"
    error_handlers: dict[Type[Exception], Callable[[Exception], Any]]
    request_handlers: dict[Type[Request], Callable[[Request], Any]]


class _RouteMetadata:
    class __metadata__(RouteMetadata):
        abstract = True
        registry = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if _RouteMetadata in cls.__bases__:
            return

        cls._setup_metadata()

    @classmethod
    def _create_new_metadata_object(cls):
        super_route = get_super_route(cls)
        cls.__metadata__ = create_metadata_type(
            super_route.__metadata__,
            abstract=False,
            request_handlers={},
            error_handlers={},
        )

    @classmethod
    def _setup_metadata(cls):
        if cls.__metadata__ is get_super_route(cls).__metadata__:
            cls._create_new_metadata_object()

        elif not issubclass(cls.__metadata__, RouteMetadata):
            cls._transform_metadata_to_metadata_type()

    @classmethod
    def _transform_metadata_to_metadata_type(cls):
        super_route = get_super_route(cls)

        if not hasattr(cls.__metadata__, "request_handlers"):
            cls.__metadata__.request_handlers = {}

        if not hasattr(cls.__metadata__, "error_handlers"):
            cls.__metadata__.error_handlers = {}

        cls.__metadata__ = create_metadata_type(
            cls.__metadata__, super_route.__metadata__
        )


class RouteMCS(type):
    methods: MethodsCollection
    name: str
    path: str

    def __repr__(cls):
        path, name, methods = cls.path, cls.name, cls.methods.names
        return f"<Route:{cls.__name__} {path=} {name=} {methods=}>"


class Route(Generic[RequestType], _RouteMetadata, TypeMatchable, metaclass=RouteMCS):
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

    methods: MethodsCollection
    name: str
    path: str

    def __init_subclass__(cls, **kwargs):
        """Setup the route class building the route meta, scanning for request & error handlers, and ensuring that
        concrete routes have a path and route handlers."""
        super().__init_subclass__(**kwargs)
        cls._setup_route()
        cls._scan_for_handlers()
        cls._validate_route_object()
        cls._register_route()

    async def __call__(self, scope, receive, send):
        """Handle a request, calling the appropriate handler function and capturing any handleable exceptions."""
        async with ExceptionHandlerContext(self) as error_handler:
            await self._handle(scope, receive, send)

        if error_handler:
            await error_handler(scope, receive, send)

    async def _handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request.factory(scope)
        if type(request) not in self.__metadata__.request_handlers:
            raise Exception(
                f"Request type {type(request)} not handled by {self.__class__.__qualname__}"
            )

        handler_registry = self.__metadata__.request_handlers
        request_type = type(request)
        response = await handler_registry[request_type](self, request)
        await response(scope, receive, send)

    @classmethod
    def register_routes(cls, router: Router):
        """Register all routes in the route registry with the given router."""
        apply(router.add_route).to(cls.__metadata__.registry)

    @classmethod
    def _add_handlers(cls, function, handler_types, container):
        for handler_type in handler_types:
            container[handler_type] = function

    @classmethod
    def _register_handlers(cls, function, *handler_types):
        if all(issubclass(handler, Request) for handler in handler_types):
            cls._add_handlers(
                function, handler_types, cls.__metadata__.request_handlers
            )

        elif all(issubclass(handler, Exception) for handler in handler_types):
            cls._add_handlers(function, handler_types, cls.__metadata__.error_handlers)

    @classmethod
    def _register_route(cls):
        if cls.__metadata__.abstract:
            return

        cls.__metadata__.registry.add(cls)

    @classmethod
    def _scan_for_handlers(cls):
        for function in get_functions(cls):
            handler_type = get_handler_type(function)
            match handler_type:
                case Option.Value(type() as ht) if issubclass(ht, (Request, Exception)):
                    cls._register_handlers(function, ht)

                case Option.Value(UnionType() as ht):
                    cls._register_handlers(function, *get_args(ht))

        cls.methods = MethodsCollection(*cls.__metadata__.request_handlers)

    @classmethod
    def _setup_route(cls):
        if cls.__metadata__.abstract:
            return

        if not hasattr(cls, "name"):
            cls.name = cls.__qualname__.casefold()

    @classmethod
    def _validate_route_object(cls):
        if cls.__metadata__.abstract:
            return

        if not hasattr(cls, "path"):
            raise MissingRoutePath(
                f"Route subclass {cls.__qualname__} is missing a path attribute."
            )

        if not cls.methods:
            raise NoRouteHandlersFound(
                f"Route subclass {cls.__qualname__} has no request handlers."
            )


def create_metadata_type(
    *bases: Type[RouteMetadata] | Type, **properties: Any
) -> Type[RouteMetadata]:
    return cast(
        Type[RouteMetadata],
        type(
            "__metadata__",
            bases,
            properties,
        ),
    )


def get_functions(cls):
    for name, attr in vars(cls).items():
        if (
            callable(attr)
            and not isinstance(attr, MethodType)
            and not name.startswith("_")
        ):
            yield attr


def get_handler_type(function):
    arg_spec = inspect.getfullargspec(unwrap(function))
    arg_type = (
        arg_spec.annotations.get(arg_spec.args[1]) if len(arg_spec.args) > 1 else None
    )
    return Option.Value(arg_type) if arg_type else Option.Null()


def get_super_route(cls):
    for base in cls.__bases__:
        if base is Route or issubclass(base, Route):
            return base


def unwrap(function):
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__

    return function
