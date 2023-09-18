from wordlette.cms.forms import Form
from wordlette.cms.themes import Template, ThemeManager
from wordlette.configs.managers import ConfigManager
from wordlette.core.app import AppSetting
from wordlette.forms.exceptions import FormValidationError
from wordlette.forms.field_types import TextField, CheckBoxField, SubmitButton, Link
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State
from wordlette.utils.dependency_injection import inject, AutoInject, inject_dependencies


class CreateSettingsFileForm(Form):
    site_name: str @ TextField(
        name="site-name",
        id="site-name",
        required=True,
        placeholder='ex. "Bob\'s Blog" or "Paul\'s Portfolio"',
        label="What is your website's name?",
    )
    domain_name: str @ TextField(
        name="domain-name",
        id="domain-name",
        required=True,
        placeholder='ex. "bobsblog.com" or "www.paulsportfolio.com"',
        label="What is your website's domain name?",
    )
    uses_https: bool @ CheckBoxField(
        name="uses-https",
        id="uses-https",
        class_="label-inline",
        checked=True,
        label="Uses HTTPS",
    )

    buttons = (
        Link("Back", href="/"),
        SubmitButton("Next", type="submit"),
    )

    def validate_type_str_isnt_empty(self, value: str):
        if not value.strip():
            raise ValueError("Field cannot be empty")


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
        return self._create_page_template(
            form=CreateSettingsFileForm.view(),
        )

    async def create_settings_file(
        self,
        form: CreateSettingsFileForm,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        path = config.write_config_file(
            settings_filename,
            working_directory,
            {
                "site": {
                    "domain": form.domain_name,
                    "https": form.uses_https,
                    "name": form.site_name,
                }
            },
        )
        subtitle = "Your Settings Have Been Saved"
        return Template(
            "create-settings-file.html",
            title=f"Wordlette: {subtitle}",
            heading="Setup",
            subtitle=subtitle,
            created_settings_file=True,
            file_path=path,
            next_page_url=_get_next_page(),
        )

    async def handle_form_validation_errors(
        self, validation_errors: FormValidationError
    ):
        return self._create_page_template(
            form=validation_errors.form.view(),
        )

    def _create_page_template(self, **kwargs):
        subtitle = "Configure Your Website"
        return Template(
            "create-settings-file.html",
            title=f"Wordlette: {subtitle}",
            heading="Setup",
            subtitle=subtitle,
            **kwargs,
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
