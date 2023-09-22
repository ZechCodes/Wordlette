from typing import Annotated, Any, Type, TypeAlias, get_origin, get_args, Generator

from wordlette.base_exceptions import BaseWordletteException
from wordlette.models.fields import Field, FieldSchema, _not_set_
from wordlette.utils.suppress_with_capture import SuppressWithCapture

FieldName: TypeAlias = str


class ValidationError(BaseWordletteException):
    def __init__(self, model: "Model"):
        super().__init__(f"Validation errors on {type(model).__qualname__}")
        self.model = model
        for name, error in model.__validation_errors__:
            self.add_note(f"- {name}: {error}")


class ModelMCS(type):
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

            hint, field = get_args(annotation)
            if isinstance(field, FieldSchema):
                yield name, field.create_field(
                    name, hint, namespace.get(name, _not_set_)
                )

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

    def __init__(self, *args, **kwargs):
        self.__field_values__: dict[FieldName, Any] = {}
        self.__validation_errors__: dict[FieldName, Exception] = {}

        self._build_values(*args, **kwargs)

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

            else:
                continue

            if error := self.set_quiet(name, value):
                self.__validation_errors__[name] = error
