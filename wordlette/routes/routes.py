import inspect
from functools import wraps
from types import MethodType, UnionType
from typing import (
    Callable,
    Generic,
    ParamSpec,
    TypeVar,
    get_args,
    Type,
)

from bevy import get_repository
from starlette.datastructures import FormData
from starlette.responses import Response
from starlette.types import Scope, Receive, Send

from wordlette.core.exceptions import (
    MissingRoutePath,
    NoRouteHandlersFound,
    CannotHandleInconsistentTypes,
)
from wordlette.forms import Form
from wordlette.requests import Request
from wordlette.routers import Router
from wordlette.routes.exception_contexts import ExceptionHandlerContext
from wordlette.routes.exceptions import NoCompatibleFormError
from wordlette.routes.method_collections import MethodsCollection
from wordlette.routes.route_metadata import RouteMetadataSetup
from wordlette.utils.apply import apply
from wordlette.utils.dependency_injection import AutoInject
from wordlette.utils.match_types import TypeMatchable
from wordlette.utils.options import Option

P = ParamSpec("P")
RequestType = TypeVar("RequestType", bound=Request)
ExceptionType = TypeVar("ExceptionType", bound=Exception)


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


def never_abstract(func: Callable[P, None]) -> Callable[P, None]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        if args[0].__metadata__.abstract:
            return

        return func(*args, **kwargs)

    return wrapper


def unwrap(function):
    while hasattr(function, "__wrapped__"):
        function = function.__wrapped__

    return function


class RouteMCS(type):
    methods: MethodsCollection
    name: str
    path: str

    def __repr__(cls):
        if hasattr(cls, "path"):
            path, name, methods = cls.path, cls.name, cls.methods.names
            return f"<Route:{cls.__name__} {path=} {name=} {methods=}>"

        return f"<Route:Abstract:{cls.__name__}>"


class Route(
    Generic[RequestType],
    RouteMetadataSetup,
    TypeMatchable,
    AutoInject,
    metaclass=RouteMCS,
):
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
        """Set up the route class building the route meta, scanning for request & error handlers, and ensuring that
        concrete routes have a path and route handlers."""
        super().__init_subclass__(**kwargs)
        cls._setup_route()
        cls._scan_for_handlers()
        cls._setup_form_handlers()
        cls._setup_methods()
        cls._validate_route_object()
        cls._register_route()

    async def __call__(self, scope, receive, send):
        """Handle a request, calling the appropriate handler function and capturing any handleable exceptions."""
        async with ExceptionHandlerContext(self) as error_handler:
            await self._handle(scope, receive, send)

        if error_handler:
            await error_handler(scope, receive, send)

    async def process_forms(self, request: Request) -> Response:
        """Process all forms in the request body and return the response."""
        form_data = await request.form()
        match self._find_best_form_handler(form_data, type(request)):
            case Option.Value((form_type, handler)):
                return await handler(self, form_type.create_from_form_data(form_data))

            case _:
                raise NoCompatibleFormError(
                    f"Form handler for {request.name} request not found for {self.__class__.__qualname__}"
                )

    def _find_best_form_handler(
        self, form_data: FormData, method_type: Type[Request]
    ) -> Option[tuple[Type[Form], Callable[[Form], Response]]]:
        handler, highest_field_count = Option.Null(), 0
        for form, handler in self.__metadata__.form_handlers.items():
            if not form.can_handle_method(method_type):
                continue

            supported_fields = form.count_matching_fields(form_data)
            if supported_fields > highest_field_count:
                handler, highest_field_count = (
                    Option.Value((form, handler)),
                    supported_fields,
                )

            if supported_fields == len(form_data):
                break

        return handler

    async def _handle(self, scope: Scope, receive: Receive, send: Send):
        request = Request.factory(scope, receive, send)
        if type(request) not in self.__metadata__.request_handlers:
            raise Exception(
                f"Request type {type(request)} not handled by {self.__class__.__qualname__}"
            )

        handler_registry = self.__metadata__.request_handlers
        request_type = type(request)
        response = await handler_registry[request_type](self, request)
        await response(scope, receive, send)

    @classmethod
    def url(cls, **path_params):
        router: Router = get_repository().get(Router)
        return router.url_for(cls, **path_params)

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
            handler_registry = cls.__metadata__.request_handlers

        elif all(issubclass(handler, Form) for handler in handler_types):
            handler_registry = cls.__metadata__.form_handlers

        elif all(issubclass(handler, Exception) for handler in handler_types):
            handler_registry = cls.__metadata__.error_handlers

        else:
            raise cls._create_inconsistent_handler_types_exception(handler_types)

        cls._add_handlers(function, handler_types, handler_registry)

    @staticmethod
    def _create_inconsistent_handler_types_exception(handler_types):
        types = ", ".join(
            handler_type.__qualname__ for handler_type in handler_types[:~0]
        )
        types += f", and {handler_types[~0].__qualname__}"
        raise CannotHandleInconsistentTypes(
            f"A route handler cannot be registered for inconsistent types: {types} do not share a compatible common"
            f" base type."
        )

    @classmethod
    @never_abstract
    def _register_route(cls):
        cls.__metadata__.registry.add(cls)

    @classmethod
    def _scan_for_handlers(cls):
        for function in get_functions(cls):
            handler_type = get_handler_type(function)
            match handler_type:
                case Option.Value(type() as ht) if issubclass(
                    ht, (Request, Exception, Form)
                ):
                    cls._register_handlers(function, ht)

                case Option.Value(UnionType() as ht):
                    cls._register_handlers(function, *get_args(ht))

    @classmethod
    def _setup_methods(cls):
        cls.methods = MethodsCollection(*cls.__metadata__.request_handlers)

    @classmethod
    @never_abstract
    def _setup_route(cls):
        if not hasattr(cls, "name"):
            cls.name = cls.__qualname__.casefold()

    @classmethod
    @never_abstract
    def _setup_form_handlers(cls):
        methods = {
            form_type.__request_method__ for form_type in cls.__metadata__.form_handlers
        }
        for method in methods:
            if method not in cls.__metadata__.request_handlers:
                cls._register_handlers(cls.process_forms, method)

    @classmethod
    @never_abstract
    def _validate_route_object(cls):
        if not hasattr(cls, "path"):
            raise MissingRoutePath(
                f"Route subclass {cls.__qualname__} is missing a path attribute."
            )

        if not cls.methods:
            raise NoRouteHandlersFound(
                f"Route subclass {cls.__qualname__} has no request handlers."
            )
