import re
import traceback
from abc import ABC, abstractmethod
from bevy import Bevy
from bevy import Context
from inspect import signature
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.types import Receive, Scope, Send
from typing import Any, Awaitable, Callable, ParamSpec, Type, TypeAlias, TypeVar

from wordlette.bevy_utils import bind_proxy
from wordlette.exceptions import WordlettePageDoesntSupportForm
from wordlette.forms import Form
from wordlette.responses import Response
from wordlette.smart_functions import call

P = ParamSpec("P")
T = TypeVar("T", bound=type)
TForm = TypeVar("TForm", bound=Type[Form])

ErrorHandler: TypeAlias = Callable[[Exception], Awaitable[Response]]
SubmitHandler: TypeAlias = Callable[P, Awaitable[T]]


class Page(ABC, Bevy):
    path: str

    error_handlers: dict[Type[Exception], ErrorHandler]
    submit_handlers: dict[TForm, SubmitHandler]

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
    async def response(
        self, *args: P.args, **kwargs: P.kwargs
    ) -> Response | str | bytes:
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        return await bind_proxy(self.bevy.branch(), self)._handle_request(
            scope, receive, send
        )

    async def _handle_request(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope, receive)
        call_params = [request]
        try:
            if form := await self._do_form_submit(request):
                call_params.append(form)

            response = await call(
                self.response, *call_params, **scope.get("path_params", {})
            )

        except Exception as exception:
            for error_type, handler in self.error_handlers.items():
                if isinstance(exception, error_type):
                    try:
                        response = await handler.__get__(self, type(self))(exception)
                    except Exception as e:
                        response = await self.exception_handler(e)

                    break

            else:
                response = await self.exception_handler(exception)

        match response:
            case str() | bytes():
                response = HTMLResponse(response)

            case Response():
                response = await bind_proxy(self.bevy, response).create_response()

        return await response(scope, receive, send)

    async def _do_form_submit(self, request: Request) -> Any | None:
        if request.method != "POST":
            return

        form_data = await request.form()
        form_type, submit_handler = self._find_form_handler(form_data)
        if not form_type:
            raise WordlettePageDoesntSupportForm(
                "Wordlette could not find an on submit handler for the submitted form."
            )

        return await call(
            submit_handler.__get__(self, type(self)),
            request,
            form=await form_type.create(form_data),
        )

    def _find_form_handler(
        self, form_data
    ) -> tuple[TForm, SubmitHandler] | tuple[None, None]:
        for form_type, submit_handler in self.submit_handlers.items():
            if form_type.matches_form(form_data):
                return form_type, submit_handler

        return None, None

    async def exception_handler(self, exception: Exception):
        st = traceback.format_exc()
        return HTMLResponse(
            f"<h1>500 {type(exception).__name__}</h1><pre>{st}</pre>", status_code=500
        )

    @classmethod
    def register(cls, site: Starlette, context: Context):
        methods = ["get"]
        if cls.submit_handlers:
            methods.append("post")

        site.add_route(cls.path, context.bind(cls)(), methods, cls.__qualname__)
