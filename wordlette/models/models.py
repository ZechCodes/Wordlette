from datetime import datetime, date, time
from types import UnionType
from typing import (
    Annotated,
    Any,
    Type,
    TypeAlias,
    get_origin,
    get_args,
    Generator,
    Union,
    Callable,
    ParamSpec,
    TypeVar,
    TypeGuard,
)

from wordlette.base_exceptions import BaseWordletteException
from wordlette.models.auto import Auto
from wordlette.models.auto_factories import (
    get_current_datetime,
    get_current_date,
    get_current_time,
    get_unique_int,
    get_unique_float,
    get_unique_string,
    create_factory,
)
from wordlette.models.fields import Field, FieldSchema, _not_set_
from wordlette.models.validators import (
    datetime_validator,
    date_validator,
    time_validator,
    builtin_type_validator,
)
from wordlette.utils.suppress_with_capture import SuppressWithCapture

FieldName: TypeAlias = str
P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


class ValidationError(BaseWordletteException):
    def __init__(self, model: "Model"):
        super().__init__(f"Validation errors on {type(model).__qualname__}")
        self.model = model
        for name, error in model.__validation_errors__:
            self.add_note(f"- {name}: {error}")


class ModelMCS(type):
    __auto_field_factories__: "dict[Type, Callable[[Type[Model]], Callable[P, R]]]"

    def __new__(
        mcs, name: str, bases: tuple[Type, ...], namespace: dict[str, Any], **kwargs
    ):
        annotations = namespace.get("__annotations__", {})
        fields = dict(mcs.build_fields(annotations, namespace))
        namespace["__fields__"] = dict(mcs.inherit_fields(bases)) | fields
        namespace |= fields
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    @staticmethod
    def build_fields(
        annotations: dict[str, Any], namespace: dict[str, Any]
    ) -> Generator[tuple[str, Field], None, None]:
        for name, annotation in annotations.items():
            if get_origin(annotation) is not Annotated:
                continue

            default = namespace.get(name, _not_set_)
            hint, field = get_args(annotation)
            if default is _not_set_ and get_origin(hint) in {Union, UnionType}:
                match get_args(hint):
                    case (type_hint, Auto() as auto):
                        hint = type_hint
                        default = auto

                    case (type_hint, type() as auto) if issubclass(auto, Auto):
                        hint = type_hint
                        default = Auto()

                    case (type_hint, none) if is_none(none):
                        hint = type_hint
                        default = None

                    case _:
                        raise TypeError(
                            f"Unsupported type hint '{hint!r}' for {name!r}"
                        )

            if isinstance(field, FieldSchema):
                yield name, field.create_field(name, hint, default)

    def __create_auto_value_function__(cls, value_type: Type) -> Callable[[], Any]:
        return lambda: None

    @staticmethod
    def inherit_fields(
        bases: tuple[Type, ...]
    ) -> Generator[tuple[str, Field], None, None]:
        for base in bases:
            if hasattr(base, "__fields__"):
                yield from base.__fields__.items()

    def __and__(cls, other: "Type[Model]") -> "ModelMCS":
        return ModelMCS(f"Joined_{cls.__name__}_{other.__name__}", (cls, other), {})


class Model(metaclass=ModelMCS):
    __fields__: dict[FieldName, Field]
    __auto_field_factories__: dict[Type, Callable[P, R]] = {
        datetime: get_current_datetime,
        date: get_current_date,
        time: get_current_time,
        int: get_unique_int,
        float: get_unique_float,
        str: get_unique_string,
        list: create_factory(list),
        dict: create_factory(dict),
        set: create_factory(set),
        frozenset: create_factory(frozenset),
        tuple: create_factory(tuple),
        bytes: create_factory(bytes),
        bytearray: create_factory(bytearray),
    }
    __type_validators__: dict[Type, Callable[[Any], Any]] = {
        datetime: datetime_validator,
        date: date_validator,
        time: time_validator,
        int: builtin_type_validator(int),
        float: builtin_type_validator(float),
        str: builtin_type_validator(str),
        list: builtin_type_validator(list),
        dict: builtin_type_validator(dict),
        set: builtin_type_validator(set),
        frozenset: builtin_type_validator(frozenset),
        tuple: builtin_type_validator(tuple),
        bytes: builtin_type_validator(bytes),
        bytearray: builtin_type_validator(bytearray),
        memoryview: builtin_type_validator(memoryview),
    }

    def __init__(self, *args, **kwargs):
        self.__field_values__: dict[FieldName, Any] = {}
        self.__validation_errors__: dict[FieldName, Exception] = {}

        self._build_values(*args, **kwargs)

    def __get_auto_value__(self, field: Field) -> Any:
        type_hint = get_origin(field.type) or field.type
        for auto_type, func in self.__auto_field_factories__.items():
            if issubclass(type_hint, auto_type):
                return func(self)

        raise TypeError(f"Cannot create auto value for {field.type!r}")

    @classmethod
    def __validate__(cls, value: Any):
        if not isinstance(value, cls):
            raise TypeError(
                f"Expected {cls.__qualname__}, got {type(value).__qualname__}"
            )

        return value

    def __serialize__(self) -> dict[FieldName, Any]:
        return self.to_dict()

    def __eq__(self, other):
        if not isinstance(other, Model):
            raise NotImplementedError()

        if not isinstance(self, type(other)) and not isinstance(other, type(self)):
            return False

        return self.__serialize__() == other.__serialize__()

    def __repr__(self) -> str:
        return f"<{type(self).__qualname__} {self.__serialize__()}>"

    def get(self, name: str) -> Any:
        if name in self.__field_values__:
            return self.__field_values__[name]

        return self.__fields__[name].default

    def set(self, name: str, value: Any):
        field = self.__fields__[name]
        value = field.validate(value)
        self.__field_values__[name] = value

    def set_quiet(self, name: str, value: Any) -> Exception | None:
        with SuppressWithCapture(Exception) as errors:
            self.set(name, value)

        return errors.captured

    def to_dict(self) -> dict[FieldName, Any]:
        return {
            name: field.serialize(self.get(name))
            for name, field in self.__fields__.items()
        }

    @classmethod
    def raise_on_error(cls, *args, **kwargs):
        model = cls(*args, **kwargs)
        if model.__validation_errors__:
            raise ValidationError(model)

        return model

    def _build_values(self, *args, **kwargs):
        args_stack = list(reversed(args))
        for name, field in self.__fields__.items():
            if name in kwargs:
                value = kwargs[name]

            elif args_stack:
                value = args_stack.pop()

            elif field.required:
                raise TypeError(
                    f"Missing required argument {name!r} for {type(self).__qualname__}"
                )

            elif isinstance(field.default, Auto):
                value = self.__get_auto_value__(field)

            else:
                continue

            if error := self.set_quiet(name, value):
                self.__validation_errors__[name] = error


def is_none(value: Any) -> TypeGuard[None]:
    return value in {None, type(None)}
