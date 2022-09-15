class WordletteException(Exception):
    ...


class WordletteStateMachineAlreadyStarted(WordletteException):
    """Raised when start is called on a state machine that has already been started."""


class WordletteNoStarletteAppFound(WordletteException):
    """Raised when the state machine has not added a Starlette app to the current state context."""


class WordletteHostAndPortRequired(WordletteException):
    """Raised when Wordlette is launched using the CLI without setting both a host & port."""


class WordlettePortMustBeAnInteger(WordletteException):
    """Raised when Wordlette is launched using the CLI & is given an invalid port."""


class WordlettePageDoesntSupportForm(WordletteException):
    """Raised when a form is submitted to a page and the page doesn't have an on submit handler that matches it."""


class WordletteNotBoundToABevyContextError(WordletteException):
    """Raised when attempting to access the Bevy context of an object when it is not bound to a context."""
