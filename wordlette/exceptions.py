class WordletteException(Exception):
    ...


class WordletteNoTransitionFound(WordletteException):
    """Raised when attempting to transition to a state that the current state has no transitions for."""


class WordletteStateMachineAlreadyStarted(WordletteException):
    """Raised when start is called on a state machine that has already been started."""


class WordletteNoStarletteAppFound(WordletteException):
    """Raised when the state machine has not added a Starlette app to the current state context."""
