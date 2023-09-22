from abc import ABC
from typing import (
    Any,
    Callable,
    Generic,
    Self,
    Type,
    TypeAlias,
    TypeVar,
    NewType,
    overload,
)

from wordlette.utils.at_annotateds import AtAnnotation
from wordlette.utils.sentinel import sentinel

F = TypeVar("F", bound="Field")
T = TypeVar("T")

ModelType = NewType("ModelType", Any)

Validator: TypeAlias = Callable[[Any], T]
Serializer: TypeAlias = Callable[[T], Any]

_NotSet_, _not_set_ = sentinel("_NotSet_")


class AbstractFieldSchema(ABC, AtAnnotation):
    __field_type__: Type[F]

    def __init_subclass__(cls, field_type: Type[F] | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if field_type is not None:
            cls.__field_type__ = field_type

    def create_field(self, *args, **kwargs) -> F:
        return self.__field_type__(self, *args, **kwargs)

    def __repr__(self):
        return f"<{type(self).__qualname__} {self.name} {self.type}>"


class Field(Generic[T]):
    def __init__(
        self,
        schema: AbstractFieldSchema,
        name: str,
        type_: Type[T],
        default: T | _NotSet_,
        *_,
    ):
        self._schema = schema
        self._name = name
        self._type = type_
        self._default = default

        self._validators: list[Validator] = [getattr(type_, "__validate__", type_)]
        self._serializer: Serializer | None = None

    def add_validator(self, validator: Validator):
        self._validators.append(validator)

    def remove_serializer(self):
        self._serializer = None

    def serialize(self, value: T) -> Any:
        if self._serializer:
            return self._serializer(value)

        if hasattr(value, "__serialize__"):
            return value.__serialize__()

        return value

    def set_serializer(self, serializer: Serializer):
        self._serializer = serializer

    def validate(self, value: Any) -> T:
        for validator in self._validators:
            value = validator(value)

        return value

    @property
    def default(self) -> T:
        return self._default

    @property
    def name(self):
        return self._name

    @property
    def required(self):
        return self._default is _not_set_

    @property
    def type(self) -> Type[T]:
        return self._type

    @overload
    def __get__(self, instance: ModelType, owner: Type[ModelType]) -> T:
        ...

    @overload
    def __get__(self, instance: None, owner: Type[ModelType]) -> Self:
        ...

    def __get__(self, instance: ModelType | None, owner: Type[ModelType]) -> Self | T:
        if instance is None:
            return self

        return instance.get(self.name)

    def __set__(self, instance: ModelType, value: Any):
        instance.set(self.name, value)

    def __repr__(self):
        return (
            f"<{type(self).__qualname__}"
            f" name={self.name!r}"
            f" type={self.type.__qualname__}"
            f" default={self.default!r}>"
        )


class FieldSchema(AbstractFieldSchema, field_type=Field):
    def create_field(
        self, name: str, type_: Type[T], default: T | _NotSet_ = _not_set_
    ) -> Field[T]:
        return super().create_field(name, type_, default)
