from inspect import get_annotations
from typing import (
    Type,
    TypeVar,
    cast,
    Annotated,
    Any,
    Callable,
    ParamSpec,
    Iterator,
    Self,
)

from wordlette.forms.elements import Element
from wordlette.utils.annotated_aggregator import AnnotatedAggregator
from wordlette.utils.sentinel import sentinel

NotSet, not_set = sentinel("NotSet")
P = ParamSpec("P")
T = TypeVar("T")


class ConverterScanner:
    def scan(self, cls: Type) -> dict[Type, str]:
        return dict(self._scan(cls))

    def _scan(self, cls: Type) -> Iterator[tuple[Type, str]]:
        for name, return_type in self._get_converter_return_types(cls):
            if return_type is not None:
                yield return_type, name

    def _get_converter_return_types(self, cls) -> Iterator[tuple[str, Type[T] | None]]:
        for name, method in vars(cls).items():
            if callable(method) and self._valid_name(name):
                yield name, self._get_return_type(method)

    def _get_return_type(self, method: Callable[[P], Type[T]]) -> Type[T] | None:
        return get_annotations(method).pop("return", None)

    def _valid_name(self, name: str) -> bool:
        return name.startswith("convert_")


class FieldMCS(type):
    def __rmatmul__(cls, other: T) -> T:
        return cast(T, Annotated[other, cls])


class Field(metaclass=FieldMCS):
    __converters__: dict[Type, str] = {}

    def __init_subclass__(
        cls, converter_scanner: Type[ConverterScanner] = ConverterScanner, **kwargs
    ):
        super().__init_subclass__(**kwargs)
        cls.__converters__ = cls._scan_for_converters(converter_scanner)

    @classmethod
    def _scan_for_converters(
        cls, scanner_type: Type[ConverterScanner]
    ) -> dict[Type, str]:
        return getattr(cls, "__converters__", {}) | scanner_type().scan(cls)

    def __init__(
        self,
        type_hint: Type[T] | None = None,
        default: T | NotSet = not_set,
        label: str | Element | NotSet = not_set,
        **attrs,
    ):
        self.attrs = attrs
        self.default = default
        self.label = label
        self.optional = False
        self.type_hint = type_hint

    def __rmatmul__(self, other: T) -> T:
        return cast(T, AnnotatedAggregator[other, self])

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.get_field_value(self.name)

    @property
    def name(self) -> str:
        return self.attrs.get("name", "")

    @property
    def required(self) -> bool:
        return not self.optional and self.default is not_set

    def compose(self, value: Any | NotSet = not_set) -> Element:
        from wordlette.forms.elements import InputElement

        params = self.attrs.copy()
        if value is not not_set:
            params["value"] = value

        if self.required:
            params["required"] = True

        return InputElement(**params)

    def compose_label(self) -> Element | None:
        from wordlette.forms.elements import LabelElement

        match self.label:
            case LabelElement():
                return self.label

            case str() as body:
                return LabelElement(
                    body, **self._filter_and_clean_params(for_=self.attrs["id"])
                )

            case _:
                return None

    def convert(self, value: Any) -> T:
        converter_name = self.__converters__.get(self.type_hint)
        converter = getattr(self, converter_name) if converter_name else self.type_hint
        return converter(value)

    def set_missing(self, **kwargs) -> Self:
        self.default = kwargs.pop("default", self.default)
        self.optional = kwargs.pop("optional", self.optional)
        self.type_hint = kwargs.pop("type_hint", self.type_hint)

        self.attrs |= {k: v for k, v in kwargs.items() if k not in self.attrs}
        return self

    def validate(self, value: T):
        return

    def _filter_and_clean_params(self, **kwargs):
        return {k.rstrip("_"): v for k, v in kwargs.items() if v is not not_set}

    @classmethod
    def from_type(cls, type_hint: "Type[Field]", **config) -> "Field":
        return cls(type_hint=type_hint, **config)
