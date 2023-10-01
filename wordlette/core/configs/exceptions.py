from wordlette.base_exceptions import BaseWordletteException


class ConfigCannotCreateFiles(BaseWordletteException):
    """Raised when a config handler cannot be used to create a file."""

    name = "Cannot Create Config Files"


class ConfigCannotLoadFiles(BaseWordletteException):
    """Raised when a config handler cannot be used to load a file."""

    name = "Cannot Load Config Files"
