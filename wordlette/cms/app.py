from bevy import get_repository

from wordlette.app import WordletteApp
from wordlette.app.states import LoadingConfig
from wordlette.cms.states import BootstrapState
from wordlette.configs.managers import ConfigManager
from wordlette.middlewares.state_router import StateRouterMiddleware
from wordlette.state_machines import StateMachine


def _create_config_manager():
    from wordlette.configs.json_handlers import JsonHandler
    from wordlette.configs.toml_handlers import TomlHandler
    from wordlette.configs.yaml_handlers import YamlHandler

    handlers = [JsonHandler]
    if TomlHandler.supported():
        handlers.append(TomlHandler)

    if YamlHandler.supported():
        handlers.append(YamlHandler)

    return ConfigManager(handlers)


def _create_state_router(call_next):
    repo = get_repository()
    repo.set(ConfigManager, _create_config_manager())
    return StateRouterMiddleware(
        call_next,
        statemachine=StateMachine(BootstrapState.goes_to(LoadingConfig)),
    )


def create_cms_app():
    return WordletteApp(
        middleware=[_create_state_router],
    )
