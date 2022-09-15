from bevy.providers import TypeProvider
from typing import Protocol, Type, TypeVar

from .config import Config


class ConfigModelProtocol(Protocol):
    __config_table__: str = ""


M = TypeVar("M", bound=ConfigModelProtocol)


class ConfigProvider(TypeProvider, priority="high"):
    def create(self, model: Type[M], *args, add: bool = False, **kwargs) -> M:
        config: Config = self.bevy.get(Config)
        model = config.populate_model(self.bevy.bind(model))
        if add:
            self.add(model)

        return model

    def supports(self, obj) -> bool:
        return hasattr(obj, "__config_table__")
