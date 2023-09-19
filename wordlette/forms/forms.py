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
    Iterable,
    ParamSpec,
)

from starlette.datastructures import FormData

import wordlette.forms
from wordlette.forms.exceptions import FormValidationError
from wordlette.forms.field_types import SubmitButton, Button
from wordlette.forms.fields import Field, NotSet, not_set
from wordlette.forms.views import FormView
from wordlette.requests import Request
from wordlette.utils.contextual_methods import contextual_method

P = ParamSpec("P")
F = TypeVar("F", bound="Form")
T = TypeVar("T")
Validator: TypeAlias = Callable[[T], None]


class FieldScanner:
    def __init__(self, form: "Type[Form]"):
        self.form = form
        self.fields = {}

    def scan(self):
        for name, type_hint in get_annotations(self.form).items():
            if not name.startswith("_"):
                self.fields[name] = self._setup_form_field(name, type_hint)

    def _setup_form_field(self, name: str, hint: Type[Field] | T) -> Field:
        params = {"type_hint": hint}
        if hasattr(self.form, name):
            params["value"] = params["default"] = getattr(self.form, name)

        construct: Callable[[P], Field] = Field.from_type
        if _is_annotated_field(hint):
            params["type_hint"], field = get_args(hint)
            construct = field.set_missing

            if isinstance(field, type):
                return field(**params)

            html_name = name.replace("_", "-").casefold()
            if field.label is not not_set:
                params["id"] = field.attrs.get("name") or html_name

            params["name"] = field.attrs.get("id") or html_name

        if get_origin(params["type_hint"]) is UnionType:
            args = get_args(params["type_hint"])
            if len(args) > 1 and not isinstance(None, args[1]):
                raise TypeError(
                    f"Form field's may not have more than one annotated type. Got {len(args)} annotations."
                )

            params["type_hint"] = args[0]
            params["optional"] = type(None) in args
            params.setdefault("default", None)

        return construct(**params)


def _is_annotated_field(hint) -> bool:
    if get_origin(hint) is not Annotated:
        return False

    _, field = get_args(hint)
    if isinstance(field, type):
        return issubclass(field, Field)

    return isinstance(field, Field)


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
    __form_view_type__: Type[FormView]

    buttons: Iterable[Button] = (SubmitButton("Submit"),)

    def __init_subclass__(
        cls,
        method: Type[Request] = Request.Post,
        field_scanner: Type[FieldScanner] | None = None,
        validator_scanner: Type[ValidatorScanner] | None = None,
        view: Type[FormView] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        cls.__request_method__ = method
        cls.__form_view_type__ = view or getattr(cls, "__form_view_type__", FormView)
        cls._setup_form_fields(field_scanner or FieldScanner)
        cls._setup_buttons()
        cls._setup_validators(validator_scanner or ValidatorScanner)

    def __init__(self, *args, **kwargs):
        self.__field_values__ = {}
        self._load_fields(*args, **kwargs)

        if errors := self._validate_fields():
            raise self._create_validation_exception(errors)

    def get_field_value(self, name: str) -> Any | NotSet:
        field_name = self.__form_field_names__[name]
        field = self.__form_fields__[field_name]
        return self.__field_values__.get(field_name, field.default)

    @contextual_method
    def view(self) -> FormView:
        return self.__form_view_type__(
            self.__form_fields__,
            self.buttons,
            self.__field_values__,
            self._validate_fields(),
        )

    @view.classmethod
    def view(cls) -> FormView:
        return cls.__form_view_type__(
            cls.__form_fields__,
            cls.buttons,
            {},
            {},
        )

    def _load_fields(self, *args, **kwargs):
        required_fields = [
            field for field in self.__form_fields__.values() if field.required
        ]
        positional_args = list(reversed(args))
        for name, field in self.__form_fields__.items():
            if name in kwargs:
                value = kwargs[name]
            elif positional_args:
                value = positional_args.pop()
            elif field in required_fields:
                raise TypeError(
                    f"{type(self).__qualname__} is missing a value for the required field {name!r}"
                )
            else:
                continue

            self.__field_values__[name] = field.convert(value)

    def _validate_fields(self) -> dict[str, Exception]:
        validation_errors = {}
        for name, value in self.__field_values__.items():
            try:
                self._validate_field(name, value)
            except Exception as e:
                validation_errors[self.__form_fields__[name].name] = e

        return validation_errors

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
    def _setup_buttons(cls):
        if isinstance(cls.buttons, Button):
            cls.buttons = (cls.buttons,)

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
        if len(data) < len(cls.__form_fields__) or any(
            name not in data for name in cls.__form_field_names__
        ):
            return 0

        return len(cls.__form_fields__)

    def _create_validation_exception(self, errors):
        error_count = "an error"
        if len(errors) > 1:
            error_count = f"{len(errors):,} errors"

        return FormValidationError(
            f"Form validation failed with {error_count}.", errors, self
        )


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
