from __future__ import annotations

from typing import Any, Type, TypeVar

from .models import Field

TField = TypeVar("TField", bound=Field)


class QueryFilter:
    def __and__(self, query_filter: QueryFilter) -> AndFilter:
        match query_filter:
            case QueryFilter():
                return AndFilter(self, query_filter)
            case _:
                raise NotImplemented()

    def __or__(self, query_filter: QueryFilter) -> OrFilter:
        match query_filter:
            case QueryFilter():
                return OrFilter(self, query_filter)
            case _:
                raise NotImplemented()


class AndFilter(QueryFilter):
    def __init__(self, *filters: QueryFilter):
        self.filters = tuple(self._process_filters(filters))

    @staticmethod
    def _process_filters(filters: tuple[QueryFilter]):
        for query_filter in filters:
            match query_filter:
                case AndFilter() as and_filter:
                    yield from and_filter.filters
                case _:
                    yield query_filter


class OrFilter(QueryFilter):
    def __init__(self, *filters: QueryFilter):
        self.filters = tuple(self._process_filters(filters))

    @staticmethod
    def _process_filters(filters: tuple[QueryFilter]):
        for query_filter in filters:
            match query_filter:
                case OrFilter() as or_filter:
                    yield from or_filter.filters
                case _:
                    yield query_filter


class AnyOfFilter(QueryFilter):
    def __init__(self, field: Type[TField], *values: Any):
        self.field = field
        self.values = values


class ValueFilter(QueryFilter):
    def __init__(self, field: Type[TField], value: Any):
        self.field = field
        self.value = value


class ContainsFilter(ValueFilter):
    pass


class StartsWithFilter(ValueFilter):
    pass


class EndsWithFilter(ValueFilter):
    pass


class GreaterThanFilter(ValueFilter):
    pass


class GreaterThanOrEqualFilter(ValueFilter):
    pass


class LessThanFilter(ValueFilter):
    pass


class LessThanOrEqualFilter(ValueFilter):
    pass


class EqualFilter(ValueFilter):
    pass


class NotEqualFilter(ValueFilter):
    pass
