from bevy import inject, dependency

from wordlette.cms.theming import Template, ThemeManager
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State


class _SetupRoute(Route):
    class __metadata__:
        abstract = True
        registry = set()


class Index(_SetupRoute):
    path = "/"

    async def get(self, request: Request.Get):
        return Template(
            "index.html", title="Wordlette", subtitle="Setting Up Your Site"
        )


class CreateSettingsFile(_SetupRoute):
    path = "/create-settings-file"

    async def get_setup_page(self, _: Request.Get):
        return Template(
            "create-settings-file.html",
            title="Wordlette",
            subtitle="Create Settings File",
        )


class SetupComplete(_SetupRoute):
    path = "/setup-complete"

    async def get_setup_page(self, _: Request.Get):
        return Template(
            "setup-complete.html",
            title="Wordlette",
            subtitle="Setup Complete",
        )


class Setup(State):
    @inject
    async def enter_state(
        self,
        route_manager: RouteManager = dependency(),
        theme_manager: ThemeManager = dependency(),
    ):
        theme_manager.set_theme(theme_manager.wordlette_res / "themes" / "setup")
        _SetupRoute.register_routes(route_manager.router)
