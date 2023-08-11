from wordlette.app.app import WordletteApp
from wordlette.configs.managers import ConfigManager
from wordlette.middlewares.router_middleware import RouterMiddleware


def app(*args, **kwargs) -> WordletteApp:
    from wordlette.state_machines import StateMachine
    from wordlette.app.states import Starting, SettingUp, Serving

    return WordletteApp(
        middleware=[RouterMiddleware],
        state_machine=StateMachine(
            Starting.goes_to(SettingUp, when=SettingUp.needs_setup),
            Starting.goes_to(Serving),
        ),
    )


def _create_config_manager():
    from wordlette.configs.json_handlers import JsonHandler
    from wordlette.configs.toml_handlers import TomlHandler
    from wordlette.configs.yaml_handlers import YamlHandler

    manager = ConfigManager([JsonHandler])
    for handler in [TomlHandler, YamlHandler]:
        if handler.supported():
            manager.add_handler(handler)

    return manager
