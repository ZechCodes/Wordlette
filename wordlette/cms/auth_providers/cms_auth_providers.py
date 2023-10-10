from typing import Any, TypeVar

from wordlette.cms.forms import Form
from wordlette.cms.themes.components import Component
from wordlette.users.auth_providers import BaseAuthProvider

T = TypeVar("T", bound=Any)


class BaseCMSAuthProvider(BaseAuthProvider, auto_register=False):
    create_account_button: Component
    create_account_form: Form
    login_button: Component
    login_form: Form
    setup_form: Form | None

    def __init_subclass__(
        cls,
        auto_register=True,
        create_account_button: Component | None = None,
        create_account_form: Form | None = None,
        login_button: Component | None = None,
        login_form: Form | None = None,
        setup_form: Form | None = None,
        **kwargs,
    ):
        super().__init_subclass__(auto_register=auto_register, **kwargs)

        cls.create_account_button = cls._get_value(
            "create_account_button", create_account_button
        )
        cls.login_button = cls._get_value("login_button", login_button)

        cls.create_account_form = cls._get_value("create_account_form", login_form)
        cls.login_form = cls._get_value("login_form", login_form)
        cls.setup_form = cls._get_value("setup_form", setup_form, optional=True)

    @classmethod
    def _get_value(
        cls, name: str, override_value: T | None, optional: bool = False
    ) -> T | None:
        if override_value is not None:
            return override_value

        if (value := getattr(cls, name, None)) is None and not optional:
            raise ValueError(f"{cls.__name__} must have an attribute {name!r}")

        return value
