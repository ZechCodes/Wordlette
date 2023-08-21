from types import EllipsisType
from typing import Any, ParamSpec, Iterable

P = ParamSpec("P")


class ExpandDict:
    """Takes any dict of str/value pairs and returns a callable that takes any number of keyword arguments. It returns a
    generator which yields all values of keys that match the keyword arguments. The value assigned to each keyword arg
    acts as a default value when the dict does not have a matching key. If the value is assigned Ellispsis/... then the
    key is required to be in the dict and a KeyError is raised when it is not found.

    Example:
        >>> a, b = ExpandDict({"a": 1}).get_values(a=..., b=2)
        >>> a, b
        (1, 2)
    """

    def __init__(self, dict_: dict[str, Any]):
        self.dict = dict_

    def get_values(self, **values) -> Iterable[Any]:
        return map(self._value_getter, values.items())

    def _value_getter(self, item: tuple[str, Any]) -> Any:
        match item:
            case (key, EllipsisType()):
                return self._get_required(self.dict, key)

            case (key, default):
                return self._get_optional(self.dict, key, default)

    @staticmethod
    def _get_optional(dict_: dict[str, Any], key: str, default: Any) -> Any:
        return dict_.get(key, default)

    @staticmethod
    def _get_required(dict_: dict[str, Any], key: str) -> Any:
        if key not in dict_:
            raise KeyError(
                f"Could not destructure the dict because it does not have a key {key!r}"
            )

        return dict_[key]


def from_dict(dict_: dict[str, Any]) -> ExpandDict:
    return ExpandDict(dict_)
