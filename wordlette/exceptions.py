class WordletteException(Exception):
    ...


class WordletteTransitionImpossible(WordletteException):
    """Raised when attempting to transition to a state that the current state has no transitions for."""


class WordletteTransitionFailed(WordletteException):
    """Raised when a transition fails with an exception."""


class WordletteDeadendState(WordletteException):
    """Raised when the statemachine is asked to transition to a state that has no transitions."""


class WordletteNoSuchState(WordletteException):
    """Raised when a state transition is requested to a state that doesn't exist."""
