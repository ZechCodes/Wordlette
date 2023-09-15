import wordlette.forms
from wordlette.base_exceptions import BaseWordletteException


class FormValidationError(BaseWordletteException):
    """Raised when a form fails to validate."""

    def __init__(
        self, message: str, errors: dict[str, Exception], form: "wordlette.forms.Form"
    ):
        super().__init__(message)
        self.errors = errors
        self.form = form

        for field_name, error in errors.items():
            self.add_note(f"{field_name} - {error}")

    @property
    def name(self):
        return f"Form Validation Error{'s' if len(self.errors) > 1 else ''}"
