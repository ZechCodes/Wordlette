from pathlib import Path
from typing import Annotated

from bevy import get_repository

from wordlette.cms.extensions.error_pages import ErrorPages
from wordlette.cms.states.setup import Setup
from wordlette.configs.managers import ConfigManager
from wordlette.core import WordletteApp
from wordlette.middlewares.router_middleware import RouterMiddleware
from wordlette.state_machines import StateMachine


def _get_config_handlers():
    from wordlette.configs import JsonHandler, TomlHandler, YamlHandler

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
    repository.set(
        Annotated[Path, "package-resources"], Path(__file__).parent / "resources"
    )

    repository.set(ConfigManager, ConfigManager(_get_config_handlers()))


def create_app(**settings):
    _setup_repository()
    return WordletteApp(
        extensions=[ErrorPages],
        middleware=[RouterMiddleware],
        state_machine=StateMachine(Setup),
        settings=settings,
    )
