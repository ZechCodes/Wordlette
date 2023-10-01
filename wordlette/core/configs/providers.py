from typing import Type, TypeVar

from bevy.options import Option, Value
from bevy.provider_state import ProviderState
from bevy.providers import TypeProvider
from bevy.providers.provider import NotSupported

from wordlette.core.configs import ConfigModel
from wordlette.core.configs.managers import ConfigManager

T = TypeVar("T", bound=ConfigModel)


class ConfigProvider(TypeProvider):
    def create(self, key: Type[T], cache: ProviderState) -> Option[T]:
        if not self.supports(key, cache):
            return NotSupported(f"{type(self)!r} does not support {key!r}")

        if key in cache:
            return Value(cache[key])

        manager: ConfigManager = cache.repository.get(ConfigManager)
        try:
            model = manager.get(key.__config_key__, key, None)
        except TypeError as e:
            model = None

        if model and key.__bevy_allow_caching__:
            print(">>> ConfigProvider.create", key, "caching")
            cache[key] = model

        return Value(model)

    def supports(self, key, _) -> bool:
        return isinstance(key, type) and issubclass(key, ConfigModel)
