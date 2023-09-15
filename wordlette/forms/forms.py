from collections import defaultdict
from inspect import get_annotations
from itertools import chain
from types import UnionType, MethodType
from typing import (
    Annotated,
    Any,
    Callable,
    Hashable,
    Sequence,
    Type,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
)

from starlette.datastructures import FormData

import wordlette.forms
from wordlette.forms import Field
from wordlette.forms.fields import FieldConfig
from wordlette.requests import Request

F = TypeVar("F", bound="Form")
T = TypeVar("T")
Validator: TypeAlias = Callable[[T], None]


class FieldScanner:
    def __init__(self, form: "Type[Form]"):
        self.form = form
        self.fields = {}

    def scan(self):
        for name, type_hint in get_annotations(self.form).items():
            self.fields[name] = self._setup_form_field(name, type_hint)

    def _setup_form_field(self, name: str, hint: Type[Field[T]] | T) -> Field[T]:
        type_hint = hint
        match hint:
            case Field.matches_type():
                field_type = hint

            case _:
                field_type = Field

        params = {}
        match getattr(self.form, name, None):
            case FieldConfig(config):
                params |= config

            case default if hasattr(self.form, name):
                params["default"] = default

        return field_type(params.pop("name", name), type_hint, **params)


class ValidatorScanner:
    def __init__(self, cls: "Type[Form]", field_names: Sequence[str]):
        self.cls = cls
        self.field_names = field_names
        self.validators = defaultdict(list)
        self.type_validators = defaultdict(list)

    def scan(self):
        for name in vars(self.cls):
            attr = getattr(self.cls, name)
            if not callable(attr):
                continue

            if name.startswith("validate_type"):
                self._process_type_validator(attr)

            elif name.startswith("validate_"):
                self._process_validator(attr, name)

    def _get_matching_field_name(self, name: str) -> str | None:
        for field_name in self.field_names:
            if name.startswith(f"validate_{field_name}"):
                return field_name

    def _process_validator(self, validator: Validator, name: str):
        field_name = self._get_matching_field_name(name)
        self.validators[field_name].append(validator)

    def _process_type_validator(self, validator: Validator):
        for type_ in self._get_type_validator_types(validator):
            self.type_validators[type_].append(validator)

    def _get_type_validator_types(self, validator: Validator) -> list[Type]:
        annotations = get_annotations(validator)
        annotation = next(iter(annotations.values()))
        origin = get_origin(annotation)
        if origin is UnionType:
            args = get_args(annotation)
            if args[~0] is None:
                args = args[:~0]

            types = list(args)

        else:
            types = [annotation]

        return [
            get_args(type_)[0] if get_origin(type_) is Annotated else type_
            for type_ in types
        ]


class Form:
    __form_fields__: dict[str, Field]
    __form_field_names__: dict[str, str]
    __validators__: dict[str, list[Validator]] = {}
    __type_validators__: dict[Type, list[Validator]] = {}
    __request_method__: Type[Request]

    def __init_subclass__(
        cls,
        method: Request = Request.Post,
        field_scanner: Type[FieldScanner] | None = None,
        validator_scanner: Type[ValidatorScanner] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        cls.__request_method__ = method
        cls._setup_form_fields(field_scanner or FieldScanner)
        cls._setup_validators(validator_scanner or ValidatorScanner)

    def __init__(self, *args, **kwargs):
        self.__field_values__ = {}
        self._load_fields(*args, **kwargs)
        self._validate_fields()

    def get_field_value(self, name: str) -> Any:
        return self.__field_values__[self.__form_field_names__[name]]

    def _load_fields(self, *args, **kwargs):
        if len(self.__form_fields__) != len(args) + len(kwargs):
            raise TypeError(
                f"Expected {len(self.__form_fields__)} arguments, got {len(args) + len(kwargs)}"
            )

        names = list(self.__form_fields__.keys())
        for name, value in kwargs.items():
            if name not in names:
                raise TypeError(f"Unexpected keyword argument {name}")

            self.__field_values__[name] = value
            names.remove(name)

        for name, value in zip(names, args):
            self.__field_values__[name] = value

    def _validate_fields(self):
        for name, value in self.__field_values__.items():
            self._validate_field(name, value)

    def _validate_field(self, name: str, value: Any):
        field = self.__form_fields__[name]
        for validator in chain([field.validate], self.__validators__.get(name, ())):
            if not isinstance(validator, MethodType):
                validator = MethodType(validator, self)

            validator(value)

        for type_, validators in self.__type_validators__.items():
            if isinstance(value, type_):
                for validator in validators:
                    if not isinstance(validator, MethodType):
                        validator = MethodType(validator, self)

                    validator(value)

    @classmethod
    def _setup_form_fields(cls, scanner_type: Type[FieldScanner]):
        scanner = scanner_type(cls)
        scanner.scan()

        cls.__form_fields__ = scanner.fields
        cls.__form_field_names__ = {}
        for name, field in scanner.fields.items():
            setattr(cls, name, field)
            cls.__form_field_names__[field.name] = name

    @classmethod
    def _setup_validators(cls, scanner_type: Type[ValidatorScanner]):
        scanner = scanner_type(cls, cls.__form_fields__)
        scanner.scan()

        _merge_dicts_of_lists(cls.__validators__, scanner.validators)
        _merge_dicts_of_lists(cls.__type_validators__, scanner.type_validators)

    @classmethod
    def add_type_validator(
        cls, type_: Type[T], validator: Validator | None = None
    ) -> Callable[[Validator], Validator] | None:
        if not validator:

            def decorator(v: Validator) -> Validator:
                cls.add_type_validator(type_, v)
                return v

            return decorator

        cls.__type_validators__.setdefault(type_, []).append(lambda _, v: validator(v))

    @classmethod
    def can_handle_method(cls, method: Type[Request]) -> bool:
        return issubclass(method, cls.__request_method__)

    @classmethod
    def create_from_form_data(cls: Type[F], data: FormData) -> F:
        return cls(
            **{
                cls.__form_field_names__[name]: value
                for name, value in data.items()
                if name in cls.__form_field_names__
            }
        )

    @classmethod
    def count_matching_fields(cls, data: FormData) -> int:
        print(list(data))
        print(list(cls.__form_field_names__))
        if len(data) < len(cls.__form_fields__) or any(
            name not in data for name in cls.__form_field_names__
        ):
            return 0

        return len(cls.__form_fields__)


def _merge_dicts_of_lists(
    base_dict: dict[Hashable, list[Any]], update_dict: dict[Hashable, list[Any]]
):
    for key, value in update_dict.items():
        base_dict.setdefault(key, []).extend(value)


@Form.add_type_validator(int)
def validate_type_int_fits_in_a_bigint(value: int):
    if value > 2**63 - 1:
        raise wordlette.forms.ValidationError(
            "Integers must not be greater than 2^63 - 1 (largest signed 64-bit integer/bigint)"
        )

    if value < -(2**63):
        raise wordlette.forms.ValidationError(
            "Integers must not be less than -2^63 (smallest signed 64-bit integer/bigint)"
        )
