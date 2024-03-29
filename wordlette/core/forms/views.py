from typing import Iterable, Any, Type

from wordlette.core.forms import Field
from wordlette.core.forms.field_types import Button, not_set
from wordlette.core.html.elements import Element, Label
from wordlette.core.requests import Request


class FormView:
    def __init__(
        self,
        fields: dict[str, Field],
        buttons: Iterable[Button],
        values: dict[str, Any],
        errors: dict[str, Exception],
        method: Type[Request] = Request.Post,
    ):
        self._buttons = None
        self._fields = None
        self._labels = None
        self._method = method

        self.errors = errors
        self.values = {
            fields[name].attrs["name"]: value for name, value in values.items()
        }

        self.raw_buttons = buttons
        self.raw_fields = fields

    @property
    def buttons(self) -> list[Element]:
        if self._buttons is None:
            self._buttons = self._compose_buttons(self.raw_buttons)

        return self._buttons

    @property
    def fields(self) -> dict[str, Element]:
        if self._fields is None:
            self._fields = self._compose_fields(self.raw_fields, self.values)

        return self._fields

    @property
    def labels(self) -> dict[str, Label]:
        if self._labels is None:
            self._labels = self._compose_labels(self.raw_fields)

        return self._labels

    @property
    def method(self) -> str:
        return self._method.name.lower()

    def _compose_buttons(self, buttons: Iterable[Button]) -> list[Element]:
        return [button.compose() for button in buttons]

    def _compose_fields(
        self, fields: dict[str, Field], values: dict[str, Any]
    ) -> dict[str, Element]:
        return {
            field.attrs["name"]: field.compose(values.get(field.attrs["name"], not_set))
            for field in fields.values()
        }

    def _compose_labels(self, fields: dict[str, Field]) -> dict[str, Label]:
        return {field.attrs["name"]: field.compose_label() for field in fields.values()}
