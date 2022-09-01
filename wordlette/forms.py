from __future__ import annotations

from functools import cache
from starlette.datastructures import FormData
from typing import Any, get_type_hints, Type, TypeVar

FieldType = TypeVar("FieldType", bound=type)
T = TypeVar("T")


class FieldCollection:
    @cache
    def __get__(self, _: None, owner: Type[Form]) -> dict[str, Field]:
        return {}


class Field:
    def __init__(
        self,
        name: str | None = None,
        field_type: Type | None = None,
        *,
        optional: bool = False,
        owner: Type[Form] | None = None,
    ):
        self._name = name
        self._attr_name = name
        self._field_type = field_type
        self._owner: Type[Form] | None = owner
        self.optional = optional

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if self.name is None:
            self._name = value

        raise ValueError(f"{type(self).__name__}.name is already assigned {self.name}")

    @property
    def field_type(self) -> Type:
        if isinstance(self._field_type, str):
            self._field_type = get_type_hints(self._owner)[self._attr_name]

        return self._field_type

    @field_type.setter
    def field_type(self, value: str):
        if self.field_type is None:
            self._field_type = value

        raise ValueError(
            f"{type(self).__name__}.field_type is already assigned {self.field_type}"
        )

    def __get__(self, instance: Form, owner: Type[Form]) -> Any:
        return instance.form_data.get(self.name)

    def __set_name__(self, owner: Type[Form], name: str):
        self._owner = owner

        try:
            self._attr_name = self.name = name
        except ValueError:
            pass

        try:
            self.field_type = owner.__annotations__.get(name)
        except ValueError:
            pass

        owner.__fields__[self.name] = self

    def __repr__(self):
        return f"{type(self).__name__}(name={self.name!r}, field_type={self.field_type!r}, optional={self.optional})"


class Form:
    __fields__: dict[str, Field] = FieldCollection()

    def __init_subclass__(cls, **kwargs):
        for name, annotation in cls.__annotations__.items():
            if name not in cls.__fields__:
                cls.__fields__[name] = Field(name, annotation, owner=cls)
                setattr(cls, name, cls.__fields__[name])

    def __init__(self, form_data: FormData):
        self.form_data = form_data

    @classmethod
    async def create(cls: Type[T], form_data: FormData) -> T:
        return cls(form_data)

    @classmethod
    def matches_form(cls, form_data: FormData) -> bool:
        if form_data.keys() - cls.__fields__.keys():
            return False

        missing_fields = cls.__fields__.keys() - form_data.keys()
        for field_name in missing_fields:
            if not cls.__fields__[field_name].optional:
                print("NOT OPTIONAL", field_name, cls.__fields__[field_name])
                return False

        return True
