class WordletteException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        self.state = None

    def __str__(self):
        s = super().__str__()
        if self.state:
            return f"state={self.state.name}: {s}"

        return s

    def __repr__(self):
        return f"<Exception:{type(self).__name__}: {self}>"


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


class WordletteNoDatabaseDriverFound(WordletteException):
    """Raised when no database class is found in a database extension."""


class WordletteInsufficientPermissionsToView(WordletteException):
    """Raised when attempting to access a model's field that the requesting user has no permissions to access."""


class WordletteInsufficientPermissionsToChange(WordletteException):
    """Raised when attempting to modify a model's field that the requesting user has no permissions to modify."""
