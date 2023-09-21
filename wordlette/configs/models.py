from bevy import inject, dependency

from wordlette.configs.managers import ConfigManager
from wordlette.models import Model


class ConfigModel(Model):
    __config_key__: str

    def __init_subclass__(cls, **kwargs):
        cls.__config_key__ = kwargs.pop("key", getattr(cls, "__config_key__", None))
        super().__init_subclass__(**kwargs)

    @classmethod
    @inject
    def __bevy_constructor__(cls, config: ConfigManager = dependency()):
        return config.get(cls.__config_key__, cls)
