import logging
import traceback
from dataclasses import dataclass
from io import StringIO

from bevy import inject, dependency
from starlette.exceptions import HTTPException
from starlette.types import Scope

from wordlette.cms.themes import Template, ThemeManager
from wordlette.core.events import LifespanStartupEvent
from wordlette.events import Observer
from wordlette.extensions import Extension
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.utils.options import Value

logger = logging.getLogger(__name__)


@dataclass
class ExceptionObject:
    name: str
    message: str
    stacktrace: str
    notes: list[str]


class ErrorPages(Extension, Observer):
    @inject
    async def on_startup(
        self, _: LifespanStartupEvent, route_manager: RouteManager = dependency()
    ):
        logger.debug("Adding error pages")
        route_manager.add_error_page(0, self._error_page)

    @inject
    def _error_page(
        self, status_code: int, scope: Scope, theme: ThemeManager = dependency()
    ) -> Template:
        match theme.find_template(f"errors/{status_code}.html"):
            case Value():
                template_name = f"errors/{status_code}.html"

            case _:
                template_name = "errors/default.html"

        exception_name = None
        if "exception" in scope:
            exception = scope["exception"]
            exception_name = type(exception).__name__
            if isinstance(exception, HTTPException) and exception.detail is not None:
                exception_name = exception.detail
            elif hasattr(exception, "name") and exception.name is not None:
                exception_name = exception.name

        name = "An error was encountered"
        if exception_name:
            name = exception_name
        elif status_code == 404:
            name = "Page not found"

        return Template(
            template_name,
            name=name,
            title=f"{status_code} - {name}",
            path=scope["path"],
            status_code=status_code,
            exception=(
                ExceptionObject(
                    exception_name,
                    getattr(scope["exception"], "detail", str(scope["exception"])),
                    self._get_stacktrace(scope["exception"]),
                    getattr(scope["exception"], "__notes__", []),
                )
                if "exception" in scope
                else None
            ),
        )

    def _get_stacktrace(self, exception: Exception) -> str | None:
        io = StringIO()
        traceback.print_exception(exception, file=io)
        return io.getvalue()
