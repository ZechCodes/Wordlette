from wordlette.base_exception import BaseWordletteException


class MissingRoutePath(BaseWordletteException):
    """Raised when a route is missing a path."""


class NoRouteHandlersFound(BaseWordletteException):
    """Raised when a route has no registered method handlers."""
