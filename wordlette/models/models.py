from base64 import urlsafe_b64encode
from datetime import datetime, date, time, timezone
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
)
from uuid import uuid4

from wordlette.base_exceptions import BaseWordletteException
from wordlette.models.auto import AutoSet, Auto
from wordlette.models.fields import Field, FieldSchema, _not_set_
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
                    case (type_hint, None):
                        hint = type_hint
                        default = None

                    case (type_hint, AutoSet() as auto):
                        hint = type_hint
                        default = auto

                    case (type_hint, type() as auto) if issubclass(auto, Auto):
                        hint = type_hint
                        default = AutoSet

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


def create_unique_int_generator(*_):
    def get_unique_int():
        return uuid4().int

    return get_unique_int


def create_unique_float_generator(*_):
    def get_unique_float():
        return float.fromhex(uuid4().hex)

    return get_unique_float


def create_unique_string_generator(*_):
    def get_unique_string():
        return urlsafe_b64encode(str(uuid4()).encode()).decode()

    return get_unique_string


def create_get_current_datetime_func(*_):
    def get_current_datetime():
        return datetime.now(timezone.utc)

    return get_current_datetime


def create_get_current_date_func(*_):
    get_now = create_get_current_datetime_func()

    def get_current_date():
        return get_now().date()

    return get_current_date


def create_get_current_time_func(*_):
    get_now = create_get_current_datetime_func()

    def get_current_time():
        return get_now().time()

    return get_current_time


class Model(metaclass=ModelMCS):
    __fields__: dict[FieldName, Field]
    __auto_field_factories__: dict[Type, Callable[P, R]] = {
        datetime: create_get_current_datetime_func,
        date: create_get_current_date_func,
        time: create_get_current_time_func,
        int: create_unique_int_generator,
        float: create_unique_float_generator,
        str: create_unique_string_generator,
    }

    def __init__(self, *args, **kwargs):
        self.__field_values__: dict[FieldName, Any] = {}
        self.__validation_errors__: dict[FieldName, Exception] = {}

        self._build_values(*args, **kwargs)

    @classmethod
    def __create_auto_value_function__(cls, value_type: Type) -> Any:
        for auto_type, func in cls.__auto_field_factories__.items():
            if issubclass(value_type, auto_type):
                return func(cls)

        raise TypeError(f"Cannot create auto value for {value_type!r}")

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

            elif isinstance(field.default, AutoSet):
                value = field.default()

            else:
                continue

            if error := self.set_quiet(name, value):
                self.__validation_errors__[name] = error
