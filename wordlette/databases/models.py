from __future__ import annotations

from bevy import Bevy
from typing import Awaitable, Callable, Generic, Type, TypeAlias, TypeVar

from .policies import FormatPolicy, ValidationPolicy, ViewPolicy, ChangePolicy

T = TypeVar("T")

FormatFunction: TypeAlias = Callable[[T, "Field[T]"], Awaitable[T]]
ValidationFunction: TypeAlias = Callable[[T, "Field[T]"], Awaitable[None]]


class Model(Bevy):
    __field_values__: dict[str, T]

    def __init__(self):
        self.__field_values__ = {}


class Field(Generic[T]):
    def __init__(
        self,
        default: T,
        *,
        format_policy: Type[FormatPolicy] = FormatPolicy,
        format: FormatFunction | None = None,
        validation_policy: Type[ValidationPolicy] = ValidationPolicy,
        validate: ValidationFunction | None = None,
        view_policy: Type[ViewPolicy] = ViewPolicy,
        view_permission: str = "",
        change_policy: Type[ChangePolicy] = ChangePolicy,
        change_permission: str = "",
    ):
        self._default = default
        self._formatting_policy = format_policy
        self._format = format
        self._validation_policy = validation_policy
        self._validate = validate
        self._view_policy = view_policy
        self._view_permission = view_permission
        self._change_policy = change_policy
        self._change_permission = change_permission

        self._field_name = ""

    def __set_name__(self, _, name):
        self._field_name = name

    def __get__(self, model: Model, _) -> FieldValue[T]:
        return FieldValue(model, self)

    async def get_value(self, model: Model) -> T:
        view_policy: ViewPolicy = model.bevy.get(self._view_policy)
        await view_policy.enforce(self)
        return model.__field_values__[self._field_name]

    async def set_value(
        self,
        model: Model,
        value: T,
        *,
        do_validation: bool = True,
        do_formatting: bool = True,
    ):
        view_policy: ViewPolicy = model.bevy.get(self._view_policy)
        await view_policy.enforce(self)

        change_policy: ChangePolicy = model.bevy.get(self._change_policy)
        await change_policy.enforce(self)

        if do_validation:
            validation_policy: ValidationPolicy = model.bevy.get(
                self._validation_policy
            )
            await validation_policy.enforce(value, self)

        if do_formatting:
            formatting_policy: FormatPolicy = model.bevy.get(self._formatting_policy)
            value = await formatting_policy.enforce(value, self)

        model.__field_values__[self._field_name] = value


class FieldValue(Generic[T]):
    def __init__(self, model: Model, field: Field[T]):
        self.model = model
        self.field = field

    def __await__(self):
        return self.get().__await__()

    def get(self) -> Awaitable[T]:
        return self.field.get_value(self.model)

    async def set(
        self, value: T, *, do_validation: bool = True, do_formatting: bool = True
    ):
        await self.field.set_value(
            self.model, value, do_validation=do_validation, do_formatting=do_formatting
        )
