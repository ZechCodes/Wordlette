from pathlib import Path
from typing import Annotated

from bevy import get_repository

from wordlette.cms.extensions.error_pages import ErrorPages
from wordlette.cms.states.setup import Setup
from wordlette.core import WordletteApp
from wordlette.middlewares.router_middleware import RouterMiddleware
from wordlette.state_machines import StateMachine


def _setup_repository():
    repository = get_repository()
    repository.set(
        Annotated[Path, "package-resources"], Path(__file__).parent / "resources"
    )


def create_app(**settings):
    _setup_repository()
    return WordletteApp(
        extensions=[ErrorPages],
        middleware=[RouterMiddleware],
        state_machine=StateMachine(Setup),
        settings=settings,
    )
