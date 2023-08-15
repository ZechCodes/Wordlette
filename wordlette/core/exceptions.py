from wordlette.base_exception import BaseWordletteException


class InvalidExtensionOrConstructor(BaseWordletteException):
    """Raised when an invalid extension or constructor is given."""

    pass


class ConfigFileNotFound(BaseWordletteException):
    """Raised when a config file cannot be found."""

    pass
