from wordlette.cms.themes import ThemeManager, Template
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State
from wordlette.utils.dependency_injection import AutoInject, inject


class Index(Route):
    path = "/"

    async def index(self, _: Request.Get):
        return Template("index.html", title="Wordlette", subtitle="Hello World!")


class Serving(State, AutoInject):
    async def enter_state(
        self,
        route_manager: RouteManager @ inject,
        theme_manager: ThemeManager @ inject,
    ):
        self._load_route_modules()
        route_manager.create_router()
        Route.register_routes(route_manager.router)
        theme_manager.set_theme(theme_manager.wordlette_res / "themes" / "default")

    def _load_route_modules(self):
        # noinspection PyUnresolvedReferences
        import wordlette.cms.states.setup.routes
