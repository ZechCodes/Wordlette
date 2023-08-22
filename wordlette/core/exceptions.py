class BaseWordletteException(Exception):
    """Base exception for all wordlette exceptions."""

    pass


class MissingRoutePath(BaseWordletteException):
    """Raised when a route is missing a path."""


class NoRouteHandlersFound(BaseWordletteException):
    """Raised when a route has no registered method handlers."""


class InvalidExtensionOrConstructor(BaseWordletteException):
    """Raised when an invalid extension or constructor is given."""

    pass


class ConfigFileNotFound(BaseWordletteException):
    """Raised when a config file cannot be found."""

    pass
