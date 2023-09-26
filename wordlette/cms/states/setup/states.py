from contextlib import suppress

from wordlette.cms.states.setup.route_types import (
    SetupRoute,
    SetupRouteCategoryController,
)
from wordlette.cms.themes import ThemeManager
from wordlette.configs.managers import ConfigManager
from wordlette.core.app import AppSetting
from wordlette.core.exceptions import ConfigFileNotFound
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.state_machines import State
from wordlette.utils.dependency_injection import AutoInject, inject


class Setup(State, AutoInject):
    async def enter_state(
        self,
        route_manager: RouteManager @ inject,
        theme_manager: ThemeManager @ inject,
        controller: SetupRouteCategoryController @ inject,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        with suppress(ConfigFileNotFound):
            config.load_config_file(settings_filename, working_directory)

        self._load_route_modules()
        SetupRoute.register_routes(route_manager.router)
        next_route = await controller.get_next_route()
        if next_route == controller.completed_route:
            return self.cycle()

        theme_manager.set_theme(theme_manager.wordlette_res / "themes" / "setup")

    def _load_route_modules(self):
        # noinspection PyUnresolvedReferences
        import wordlette.cms.states.setup.routes
