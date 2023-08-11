from bevy import inject, dependency

from wordlette.configs.managers import ConfigManager


class ConfigModel:
    __config_key__: str

    @classmethod
    @inject
    def __bevy_constructor__(cls, config: ConfigManager = dependency()):
        return config.get(cls.__config_key__, cls)
