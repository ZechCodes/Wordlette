from typing import cast

from wordlette.cms.forms import Form
from wordlette.cms.states.setup.enums import SetupCategory, SetupStatus
from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.core.app import AppSetting
from wordlette.core.configs import ConfigManager
from wordlette.core.forms.field_types import (
    Link,
    SubmitButton,
    CheckboxGroupField,
)
from wordlette.core.requests import Request
from wordlette.core.routes.query_vars import QueryArg
from wordlette.users.auth_providers import BaseAuthProvider
from wordlette.utils.dependency_injection import inject


class SelectAuthProviderTypesForm(Form):
    authentication_types: list[str] @ CheckboxGroupField(
        options={},
        legend="Which login methods would you like to use?",
    )

    buttons = (
        Link("Back", href="/"),
        SubmitButton("Next", type="submit"),
    )


class ConfigureAuthProviders(SetupRoute, setup_category=SetupCategory.Admin):
    path = "/configure-login-methods"

    def __init__(self):
        super().__init__()
        self._exception = None

    async def setup_status(
        self,
        config: ConfigManager @ inject = None,
    ) -> SetupStatus:
        settings = config.get("authentication", default=None)
        if settings is None:
            return SetupStatus.Ready

        return SetupStatus.Complete

    async def get_setup_page(
        self,
        _: Request.Get,
        database_type: str @ QueryArg("authentication-types", None),
    ):
        form = SelectAuthProviderTypesForm
        auth_types_field: CheckboxGroupField = cast(
            CheckboxGroupField, form.__form_fields__["authentication_types"]
        )
        auth_types_field.options |= {
            driver.nice_name: driver.__qualname__
            for driver in BaseAuthProvider.__auth_provider_registry__
        }

        auth_types_field.options = dict(sorted(auth_types_field.options.items()))

        params = {}
        if self._exception:
            params["errors"] = [str(self._exception).capitalize()]
            self._exception = None

        return self._create_template(form=form, **params)

    async def save_authentication_settings(
        self,
        form: SelectAuthProviderTypesForm,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        config.config["authentication"] = {"methods": form.authentication_types}
        config.save_to_config_file(settings_filename, working_directory)
        return await self.complete()

    def _create_template(self, **kwargs):
        return Template("setup-page.html", subtitle="Configure Login Methods", **kwargs)
