from typing import Iterable, Any

from wordlette.forms import Field
from wordlette.forms.elements import Element, LabelElement
from wordlette.forms.field_types import Button, not_set


class FormView:
    def __init__(
        self,
        fields: dict[str, Field],
        buttons: Iterable[Button],
        values: dict[str, Any],
        errors: dict[str, Exception],
    ):
        self._buttons = None
        self._fields = None
        self._labels = None

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
    def labels(self) -> dict[str, LabelElement]:
        if self._labels is None:
            self._labels = self._compose_labels(self.raw_fields)

        return self._labels

    def _compose_buttons(self, buttons: Iterable[Button]) -> list[Element]:
        return [button.compose() for button in buttons]

    def _compose_fields(
        self, fields: dict[str, Field], values: dict[str, Any]
    ) -> dict[str, Element]:
        return {
            field.attrs["name"]: field.compose(values.get(field.attrs["name"], not_set))
            for field in fields.values()
        }

    def _compose_labels(self, fields: dict[str, Field]) -> dict[str, LabelElement]:
        return {field.attrs["name"]: field.compose_label() for field in fields.values()}
