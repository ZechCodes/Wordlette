from wordlette.cms.theming import Template, ThemeManager
from wordlette.configs.managers import ConfigManager
from wordlette.core.app import AppSetting
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State
from wordlette.utils.dependency_injection import inject, AutoInject, inject_dependencies


class _SetupRoute(Route):
    class __metadata__:
        abstract = True
        registry = set()


class Index(_SetupRoute):
    path = "/"

    async def get(self, request: Request.Get):
        return Template(
            "index.html",
            title="Wordlette",
            subtitle="Setting Up Your Site",
            next_page_url=_get_next_page(),
        )


class CreateSettingsFile(_SetupRoute):
    path = "/create-settings-file"

    async def get_setup_page(self, _: Request.Get):
        subtitle = "Create Your Settings File"
        return Template(
            "create-settings-file.html",
            title=f"Wordlette: {subtitle}",
            heading="Setup",
            subtitle=subtitle,
        )

    async def create_settings_file(
        self,
        request: Request.Post,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        settings = await request.form()
        path = config.write_config_file(
            settings_filename,
            working_directory,
            {
                "site": {
                    "domain": settings["domain-name"],
                    "https": settings["uses-https"].casefold() in {"on"},
                    "name": settings["site-name"],
                }
            },
        )
        subtitle = "Your Settings File Has Been Created"
        return Template(
            "create-settings-file.html",
            title="Wordlette: {subtitle}",
            heading="Setup",
            subtitle=subtitle,
            created_settings_file=True,
            file_path=path,
            next_page_url=_get_next_page(),
        )


class SetupComplete(_SetupRoute):
    path = "/setup-complete"

    async def get_setup_page(self, _: Request.Get):
        return Template(
            "setup-complete.html",
            title="Wordlette",
            subtitle="Setup Complete",
        )


class Setup(State, AutoInject):
    async def enter_state(
        self,
        route_manager: RouteManager @ inject,
        theme_manager: ThemeManager @ inject,
    ):
        theme_manager.set_theme(theme_manager.wordlette_res / "themes" / "setup")
        _SetupRoute.register_routes(route_manager.router)


@inject_dependencies
def _get_next_page(
    config: ConfigManager @ inject = None,
    router: RouteManager @ inject = None,
    settings_filename: str @ AppSetting("settings-filename") = None,
    working_directory: str @ AppSetting("working-directory") = None,
):
    settings_path = config.find_config_file(settings_filename, working_directory)
    if settings_path is None:
        return router.url_for(CreateSettingsFile)

    return router.url_for(SetupComplete)
