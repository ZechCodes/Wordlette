class BaseWordletteException(Exception):
    """Base exception for all wordlette exceptions."""

    pass


class InvalidExtensionOrConstructor(BaseWordletteException):
    """Raised when an invalid extension or constructor is given."""

    pass


class ConfigFileNotFound(BaseWordletteException):
    """Raised when a config file cannot be found."""

    pass
