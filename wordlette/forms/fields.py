from typing import Any, Type, TypeVar, Generic

from wordlette.utils.match_types import TypeMatchable

T = TypeVar("T")


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

        return instance.__field_values__[self.name]

    def validate(self, value: T):
        return
