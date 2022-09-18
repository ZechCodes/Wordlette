from bevy import Bevy, Inject, bevy_method
from typing import Generic, TypeVar

from wordlette.exceptions import (
    WordletteInsufficientPermissionsToView,
    WordletteInsufficientPermissionsToChange,
)
from wordlette.permissions import Permissions
from wordlette.policies import Policy, ValuePolicy

T = TypeVar("T")


class FormatPolicy(ValuePolicy):
    name = "BaseFormattingPolicy"

    @staticmethod
    async def rule(field: T, *_, **__) -> T:
        if field.format:
            field = await field.format(field)

        return field


class ValidationPolicy(Generic[T], Policy):
    name = "BaseValidationPolicy"

    @staticmethod
    async def rule(value: T, field):
        if field.validate:
            await field.validate(value, field)


class ViewPolicy(Generic[T], Policy, Bevy):
    name = "BaseViewPolicy"

    @staticmethod
    @bevy_method
    async def rule(field, permissions: Permissions = Inject):
        if field.view_permission and not permissions[field.view_permission]:
            raise WordletteInsufficientPermissionsToView(
                f"User must have the {field.view_permission!r} permission to view the value of {field}."
            )


class ChangePolicy(Generic[T], Policy, Bevy):
    name = "BaseChangePolicy"

    @staticmethod
    @bevy_method
    async def rule(field, permissions: Permissions = Inject):
        if field.view_permission and not permissions[field.change_permission]:
            raise WordletteInsufficientPermissionsToChange(
                f"User must have the {field.change_permission!r} permission to change the value of {field}."
            )
