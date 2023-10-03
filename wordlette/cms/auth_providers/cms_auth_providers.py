from wordlette.cms.forms import Form
from wordlette.users.auth_providers import BaseAuthProvider


class BaseCMSAuthProvider(BaseAuthProvider, auto_register=False):
    setup_form: Form | None

    def __init_subclass__(
        cls, setup_form: Form | None = None, auto_register=True, **kwargs
    ):
        cls.setup_form = cls._determine_setup_form(setup_form)

        super().__init_subclass__(**kwargs)

    @classmethod
    def _determine_setup_form(cls, setup_form: Form | None) -> Form | None:
        if setup_form is not None:
            return setup_form

        return getattr(cls, "setup_form", None)
