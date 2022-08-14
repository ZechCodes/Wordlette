class WordletteException(Exception):
    ...


class WordletteTransitionImpossible(WordletteException):
    """Raised when attempting to transition to a state that the current state has no transitions for."""


class WordletteTransitionFailed(WordletteException):
    """Raised when a transition fails with an exception."""
