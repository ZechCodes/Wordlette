from wordlette.core.exceptions import BaseWordletteException


class BaseWordletteCMSExecption(BaseWordletteException):
    """Base exception for all wordlette cms exceptions."""


class ThemeNotFound(BaseWordletteCMSExecption):
    """Raised when a theme cannot be found."""

    name = "Theme Not Found"


class TemplateNotFound(BaseWordletteCMSExecption):
    """Raised when a template cannot be found."""

    name = "Template Not Found"
