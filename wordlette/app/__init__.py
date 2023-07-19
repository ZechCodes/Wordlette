from wordlette.app.app import WordletteApp
from wordlette.configs.managers import ConfigManager


def app(*args, **kwargs) -> WordletteApp:
    from wordlette.state_machines import StateMachine
    from wordlette.app.states import (
        BootstrappingApp,
        CreatingConfig,
        ConnectingDB,
        LoadCoreExtensions,
        LoadingConfig,
        ServingApp,
    )

    return WordletteApp(
        StateMachine(
            BootstrappingApp.goes_to(LoadCoreExtensions),
            LoadCoreExtensions.goes_to(LoadingConfig),
            LoadingConfig.goes_to(ConnectingDB, when=ConnectingDB.has_database_config),
            LoadingConfig.goes_to(
                CreatingConfig, when=CreatingConfig.has_no_config_file
            ),
            CreatingConfig.goes_to(ConnectingDB),
            ConnectingDB.goes_to(ServingApp),
        ),
        config_manager=_create_config_manager(),
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
