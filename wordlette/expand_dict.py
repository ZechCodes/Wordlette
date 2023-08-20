from types import EllipsisType
from typing import Any, ParamSpec, Callable, Generator

P = ParamSpec("P")


def expand_dict(
    dict_: dict[str, Any]
) -> Callable[[P], Generator[P.kwargs, None, None]]:
    """Takes any dict of str/value pairs and returns a function that takes any number of keyword arguments. It returns a
    generator which yields all values of keys that match the keyword arguments. The value assigned to each keyword arg
    acts as a default value when the dict does not have a matching key. If the value is assigned Ellispsis/... then the
    key is required to be in the dict and a KeyError is raised when it is not found.

    Example:
        >>> a, d = expand_dict({"a": 1, "b": 2, "c": 3})(a=..., d=4)
        >>> a, d
        (1, 4)
    """

    def expand(**values: P) -> Generator[P.kwargs, None, None]:
        yield from map(lambda i: _expand(dict_, i), values.items())

    return expand


def _expand(dict_: dict[str, Any], item: tuple[str, Any]) -> tuple[str, Any]:
    match item:
        case (key, EllipsisType()):
            if key not in dict_:
                raise KeyError(
                    f"Could not destructure the dict because it does not have a key {key!r}"
                )

            return dict_[key]

        case (key, default):
            return dict_.get(key, default)
