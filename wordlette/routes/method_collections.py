from collections.abc import Set
from typing import Type, Iterator

from wordlette.requests import Request


class MethodsCollection(Set[Type[Request]]):
    def __init__(self, *methods: Type[Request]):
        self._methods = set(methods)

    @property
    def names(self):
        return [method.name for method in self]

    def __contains__(self, request: Request | Type[Request]) -> bool:
        request_type = type(request) if isinstance(request, Request) else request
        return request_type in self._methods

    def __iter__(self) -> Iterator[Type[Request]]:
        return iter(self._methods)

    def __len__(self) -> int:
        return len(self._methods)

    def __repr__(self):
        return f"<{type(self).__name__} {{{', '.join(sorted(method.name for method in self))}}}>"
