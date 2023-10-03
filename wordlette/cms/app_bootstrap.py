import logging
from pathlib import Path
from typing import Annotated

from bevy import get_repository

from wordlette.cms.auth_providers.cms_auth_providers import BaseCMSAuthProvider
from wordlette.cms.extensions.error_pages import ErrorPages
from wordlette.cms.states.serving import Serving
from wordlette.cms.states.setup import Setup
from wordlette.core import WordletteApp
from wordlette.core.configs import ConfigManager
from wordlette.core.configs.providers import ConfigProvider
from wordlette.core.middlewares.router_middleware import RouterMiddleware
from wordlette.core.sessions import SessionController
from wordlette.state_machines import StateMachine
from wordlette.users.auth_security_levels import AuthSecurityLevel

logger = logging.getLogger("CMS-Boostrap")


def _get_config_handlers():
    from wordlette.core.configs import JsonHandler, TomlHandler, YamlHandler

    yield from (
        handler
        for handler in (
            YamlHandler,
            JsonHandler,
            TomlHandler,
        )
        if not hasattr(handler, "supported") or handler.supported()
    )


def _setup_repository():
    repository = get_repository()
    repository.add_providers(ConfigProvider())
    repository.set(
        Annotated[Path, "package-resources"], Path(__file__).parent / "resources"
    )
    repository.set(ConfigManager, ConfigManager(_get_config_handlers()))

    repository.set(SessionController, SessionController.create())


def _setup_auth_providers(min_security_level: AuthSecurityLevel):
    for provider in list(BaseCMSAuthProvider.__auth_provider_registry__):
        if provider.security_level < min_security_level:
            provider.unregister_auth_provider()


def create_app(**settings):
    _setup_repository()

    debug = settings.get("debug", False)
    min_auth_security_level = settings.get(
        "min_auth_security_level",
        AuthSecurityLevel.UNSAFE if debug else AuthSecurityLevel.BASIC,
    )
    _setup_auth_providers(min_auth_security_level)

    if not debug and min_auth_security_level == AuthSecurityLevel.UNSAFE:
        message = f"Server is running with the {AuthSecurityLevel.UNSAFE.name} authentication security level."
        sub_message = "Consider increasing the security level."
        stars = "*" * (len(message) + 6)
        logger.warning(
            f"\n{stars}\n\n*  {message}  *\n\n*  {sub_message:^{len(message)}}  *\n\n{stars}"
        )

    app = WordletteApp(
        extensions=[ErrorPages],
        middleware=[RouterMiddleware],
        state_machine=StateMachine(Setup.goes_to(Serving)),
        settings=settings,
    )
    get_repository().get(SessionController).observe(app)
    return app
