from wordlette.models import Model


class ConfigModel(Model):
    __bevy_allow_caching__ = False
    __config_key__: str

    def __init_subclass__(cls, **kwargs):
        cls.__config_key__ = kwargs.pop("key", getattr(cls, "__config_key__", None))
        super().__init_subclass__(**kwargs)
