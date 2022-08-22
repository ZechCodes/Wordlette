from weakref import WeakKeyDictionary
from wordlette.routing.controllers import ControllerSchema
from wordlette.predicates import Predicate


class ControllerSchemaCollection:
    def __init__(self):
        self._cache = WeakKeyDictionary()

    def __get__(self, _, owner) -> dict[Predicate, ControllerSchema]:
        try:
            return self._cache[owner]
        except KeyError:
            self._cache[owner] = new_value = {}
            return new_value
