from wordlette.base_exceptions import BaseWordletteException


class NoCompatibleFormError(BaseWordletteException):
    """Raised when no compatible form is found for the request."""

    name = "No Compatible Form Found"
