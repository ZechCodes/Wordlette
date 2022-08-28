import re
import traceback
from abc import ABC, abstractmethod
from inspect import signature
from starlette.applications import Starlette
from starlette.responses import Response, HTMLResponse
from typing import Awaitable, Callable, ParamSpec, Type, TypeVar

P = ParamSpec("P")
T = TypeVar("T", bound=type)


class Page(ABC):
    path: str

    error_handlers: dict[Type[Exception], Callable[[Exception], Awaitable[Response]]]
    submit_handlers: dict[T, Callable[P, Awaitable[T]]]

    def __init_subclass__(cls, **kwargs):
        cls.error_handlers = getattr(cls, "error_handlers", {})
        cls.submit_handlers = getattr(cls, "submit_handlers", {})
        for name, attr in vars(cls).items():
            if re.match(
                r"on_(?:[a-zA-Z0-9][a-zA-Z0-9_]*_)?error(?:_[a-zA-Z0-9_]+)?", name
            ):
                sig = signature(attr)
                cls.error_handlers[sig.parameters["error"].annotation] = attr

            elif re.match(
                r"on_(?:[a-zA-Z0-9][a-zA-Z0-9_]*_)?submit(?:_[a-zA-Z0-9_]+)?", name
            ):
                sig = signature(attr)
                cls.submit_handlers[sig.parameters["form"].annotation] = attr

    @abstractmethod
    async def response(self, *args: P.args, **kwargs: P.kwargs) -> Response:
        ...

    async def __call__(self, *args, **kwargs):
        try:
            response = await self.response()
        except Exception as exception:
            for error_type, handler in self.error_handlers.items():
                if isinstance(exception, error_type):
                    response = await handler.__get__(self, type(self))(exception)
                    break
            else:
                response = await self.exception_handler(exception)

        return await response(*args, **kwargs)

    async def exception_handler(self, exception: Exception):
        st = traceback.format_exc()
        return HTMLResponse(f"<h1>400 {type(exception).__name__}</h1><pre>{st}</pre>")

    @classmethod
    def register(cls, app: Starlette):
        methods = ["get"]
        if cls.submit_handlers:
            methods.append("post")

        app.add_route(cls.path, cls(), methods, cls.__qualname__)
