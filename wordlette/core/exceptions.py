from wordlette.base_exceptions import BaseWordletteException


class MissingRoutePath(BaseWordletteException):
    """Raised when a route is missing a path."""

    name = "Route Path is Missing"


class NoRouteHandlersFound(BaseWordletteException):
    """Raised when a route has no registered method handlers."""

    name = "No Route Handlers Found"


class InvalidExtensionOrConstructor(BaseWordletteException):
    """Raised when an invalid extension or constructor is given."""

    name = "Invalid Extension or Constructor"


class ConfigFileNotFound(BaseWordletteException):
    """Raised when a config file cannot be found."""

    name = "Config File Not Found"


class CannotHandleInconsistentTypes(BaseWordletteException):
    """Raised when a route handler is registered to handle inconsistent types."""

    name = "Route Handlers Cannot Handle Inconsistent Types"
