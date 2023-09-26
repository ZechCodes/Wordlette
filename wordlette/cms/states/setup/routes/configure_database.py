import logging
from typing import cast

from starlette.responses import RedirectResponse

from wordlette.cms.forms import Form
from wordlette.cms.states.setup.enums import SetupCategory, SetupStatus
from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.configs.managers import ConfigManager
from wordlette.core.app import AppSetting
from wordlette.databases.drivers import DatabaseDriver
from wordlette.databases.settings_models import DatabaseSettings
from wordlette.forms.exceptions import FormValidationError
from wordlette.forms.field_types import (
    Link,
    SubmitButton,
    SelectField,
)
from wordlette.requests import Request
from wordlette.routes.query_vars import QueryArg
from wordlette.utils.dependency_injection import inject

logger = logging.getLogger(__name__)


class SelectDatabaseTypeForm(Form, method=Request.Get):
    database_type: str @ SelectField(
        label="What type of database do you want to use?",
        placeholder="Select your database",
        options={},
    )

    buttons = (
        Link("Back", href="/"),
        SubmitButton("Next", type="submit"),
    )


class ConfigureDatabase(SetupRoute, setup_category=SetupCategory.Database):
    path = "/configure-database"

    async def setup_status(
        self,
        config: ConfigManager @ inject = None,
    ) -> SetupStatus:
        if config.get("database", DatabaseSettings, None):
            logger.info("Database is configured")
            return SetupStatus.Complete

        logger.info("Database is not configured")
        return SetupStatus.Ready

    async def get_setup_page(
        self,
        _: Request.Get,
        database_type: str @ QueryArg("database-type", None)
    ):
        form = SelectDatabaseTypeForm
        db_type_field: SelectField = cast(
            SelectField, form.__form_fields__["database_type"]
        )
        db_type_field.options = {
            driver.nice_name: driver.driver_name
            for driver in DatabaseDriver.__drivers__.values()
        }
        if driver := DatabaseDriver.__drivers__.get(database_type):
            form = driver.__settings_form__

        return self._create_template(form=form)

    async def save_database_settings(
        self,
        request: Request.Post,
        database_type: str @ QueryArg("database-type", None),
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        if not (driver := DatabaseDriver.__drivers__.get(database_type)):
            return RedirectResponse(self.url())

        form_data = await request.form()
        try:
            form = driver.__settings_form__.create_from_form_data(form_data)
        except FormValidationError as exc:
            return self._create_template(form=exc.form)

        db_settings = config.config.setdefault("database", {})
        db_settings |= {
            "driver": database_type,
            "settings": form.convert_to_dict(),
        }
        config.save_to_config_file(settings_filename, working_directory)
        return await self.complete()

    def _create_template(self, **kwargs):
        return Template("setup-page.html", subtitle="Configure Database", **kwargs)
