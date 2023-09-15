from wordlette.base_exceptions import BaseWordletteException


class FormValidationError(BaseWordletteException):
    """Raised when a form fails to validate."""

    name = "Form Validation Error(s)"

    def __init__(self, message: str, errors: dict[str, Exception]):
        super().__init__(message)
        self.errors = errors
