from wordlette.configs.managers import ConfigManager
from wordlette.core.app import WordletteApp


def _create_config_manager():
    from wordlette.configs.json_handlers import JsonHandler
    from wordlette.configs.toml_handlers import TomlHandler
    from wordlette.configs.yaml_handlers import YamlHandler

    manager = ConfigManager([JsonHandler])
    for handler in [TomlHandler, YamlHandler]:
        if handler.supported():
            manager.add_handler(handler)

    return manager
