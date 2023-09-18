from typing import Iterable, Any

from wordlette.forms import Field
from wordlette.forms.field_types import Button, not_set


class FormView:
    def __init__(
        self,
        fields: dict[str, Field],
        buttons: Iterable[Button],
        values: dict[str, Any],
    ):
        self.fields = fields
        self.buttons = buttons
        self.values = values

    def compose(self):
        for name, field in self.fields.items():
            yield from field.compose(self.values.get(name, not_set))

        for button in self.buttons:
            yield from button.compose()
