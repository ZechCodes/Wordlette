import logging

from bevy import inject, dependency
from starlette.types import Scope

from wordlette.cms.theming import Template, ThemeManager
from wordlette.core.events import LifespanStartupEvent
from wordlette.events import Observer
from wordlette.extensions import Extension
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.utils.options import Value

logger = logging.getLogger(__name__)


class ErrorPages(Extension, Observer):
    def __init__(self):
        logger.debug("Initializing error pages")

    @inject
    async def on_startup(
        self, _: LifespanStartupEvent, route_manager: RouteManager = dependency()
    ):
        logger.debug("Adding error pages")
        route_manager.add_error_page(0, self._error_page)

    @inject
    def _error_page(self, status_code: int, scope: Scope, theme: ThemeManager = dependency()) -> Template:
        match theme.find_template(f"errors/{status_code}.html"):
            case Value():
                template_name = f"errors/{status_code}.html"

            case _:
                template_name = "errors/default.html"

        return Template(
            template_name,
            name="Page not found" if status_code == 404 else "An error was encountered",
            path=scope["path"],
            status_code=status_code,
        )
