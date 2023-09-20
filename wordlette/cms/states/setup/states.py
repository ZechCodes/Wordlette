from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import ThemeManager
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.state_machines import State
from wordlette.utils.dependency_injection import AutoInject, inject


class Setup(State, AutoInject):
    async def enter_state(
        self,
        route_manager: RouteManager @ inject,
        theme_manager: ThemeManager @ inject,
    ):
        self._load_route_modules()
        theme_manager.set_theme(theme_manager.wordlette_res / "themes" / "setup")
        SetupRoute.register_routes(route_manager.router)

    def _load_route_modules(self):
        # noinspection PyUnresolvedReferences
        import wordlette.cms.states.setup.routes
