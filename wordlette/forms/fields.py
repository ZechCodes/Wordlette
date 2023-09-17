from typing import Type, TypeVar, cast, Annotated, Iterable, Any

from wordlette.forms.elements import Element
from wordlette.utils.sentinel import sentinel

NotSet, not_set = sentinel("NotSet")
T = TypeVar("T")


class FieldMCS(type):
    def __rmatmul__(cls, other: T) -> T:
        return cast(T, Annotated[other, cls])


class Field(metaclass=FieldMCS):
    def __init__(self, type_hint: Type[T] | None = None, **attrs):
        self.attrs = attrs
        self.type_hint = type_hint

    def __rmatmul__(self, other: T) -> T:
        return cast(T, Annotated[other, self])

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.get_field_value(self.name)

    @property
    def name(self) -> str:
        return self.attrs.get("name", "")

    @property
    def value(self) -> T | NotSet:
        return self.attrs.get("value", not_set)

    def compose(self, value: Any | NotSet = not_set) -> Iterable[Element]:
        from wordlette.forms.field_types import TextField

        params = self.attrs.copy()
        if value is not not_set:
            params["value"] = value

        yield TextField(**params)

    def set_missing(self, **kwargs):
        self.type_hint = kwargs.pop("type_hint", self.type_hint)
        self.attrs |= {k: v for k, v in kwargs.items() if k not in self.attrs}

    def validate(self, value: T):
        return

    @classmethod
    def from_type(cls, type_hint: "Type[Field]", **config) -> "Field":
        return cls(type_hint=type_hint, **config)
