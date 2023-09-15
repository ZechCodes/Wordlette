from typing import Any, Type, TypeVar, Generic

from wordlette.utils.match_types import TypeMatchable

T = TypeVar("T")
OPTIONAL = object()


def field(name: str = OPTIONAL, type: Type[T] = OPTIONAL, **_config) -> Any:
    config = _config
    if name is not OPTIONAL:
        config["name"] = name

    if type is not OPTIONAL:
        config["type"] = type

    return FieldConfig(config)


class FieldConfig:
    __match_args__ = ("config",)

    def __init__(self, config: dict[str, Any]):
        self.config = config


class Field(Generic[T], TypeMatchable):
    def __init__(self, field_name: str, field_type: Type[T], **config):
        self.name = field_name
        self.type = field_type
        self.config = config

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.get_field_value(self.name)

    def validate(self, value: T):
        return
