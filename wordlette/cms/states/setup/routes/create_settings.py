from wordlette.cms.forms import Form
from wordlette.cms.states.setup.enums import SetupCategory, SetupStatus
from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.core.app import AppSetting
from wordlette.core.configs import ConfigManager
from wordlette.core.forms import FormValidationError
from wordlette.core.forms.field_types import (
    Link,
    SubmitButton,
    CheckBoxField,
    TextField,
)
from wordlette.core.requests import Request
from wordlette.utils.dependency_injection import inject


class CreateSettingsFileForm(Form):
    site_name: str @ TextField(
        placeholder='ex. "Bob\'s Blog" or "Paul\'s Portfolio"',
        label="What is your website's name?",
    )
    domain_name: str @ TextField(
        placeholder='ex. "bobsblog.com" or "www.paulsportfolio.com"',
        label="What is your website's domain name?",
    )
    force_https: bool @ CheckBoxField(
        classes=["label-inline"],
        checked=True,
        label="Force HTTPS",
    )

    buttons = (
        Link("Back", href="/"),
        SubmitButton("Next", type="submit"),
    )

    def validate_type_str_isnt_empty(self, value: str):
        if not value.strip():
            raise ValueError("Field cannot be empty")


class CreateSettingsFile(SetupRoute, setup_category=SetupCategory.Config):
    path = "/create-settings-file"

    async def setup_status(
        self,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ) -> SetupStatus:
        if config.get("site", default=None):
            return SetupStatus.Complete

        return SetupStatus.Ready

    async def get_setup_page(self, _: Request.Get):
        return self._create_page_template(
            form=CreateSettingsFileForm,
        )

    def create_settings_file(
        self,
        form: CreateSettingsFileForm,
        config: ConfigManager @ inject,
        settings_filename: str @ AppSetting("settings-filename"),
        working_directory: str @ AppSetting("working-directory"),
    ):
        settings = config.config.setdefault("site", {})
        settings |= {
            "name": form.site_name,
            "domain": form.domain_name,
            "https": form.force_https,
        }
        config.save_to_config_file(settings_filename, working_directory)
        return self.complete()

    async def handle_form_validation_errors(
        self, validation_errors: FormValidationError
    ):
        return self._create_page_template(
            form=validation_errors.form,
        )

    def _create_page_template(self, **kwargs):
        subtitle = "Configure Your Website"
        return Template(
            "setup-page.html",
            title=f"Wordlette: {subtitle}",
            heading="Setup",
            subtitle=subtitle,
            **kwargs,
        )
