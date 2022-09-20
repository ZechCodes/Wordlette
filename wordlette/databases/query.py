from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

from .filters import QueryFilter
from .models import Model, Field

TModel = TypeVar("TModel", bound=Model)
TField = TypeVar("TField", bound=Field)


class Query(ABC, Generic[TModel]):
    def __init__(self, model: Type[TModel], query_filter: QueryFilter | None = None):
        self.model = model
        self.filter = QueryFilter() if query_filter is None else query_filter
        self.sort_by: list[TField] = []

    @abstractmethod
    async def delete(self):
        ...

    @abstractmethod
    async def fetch_all(self) -> QueryResult[TModel]:
        ...

    @abstractmethod
    async def fetch_one(self) -> TModel:
        ...

    @abstractmethod
    async def update(self, **changes: Any):
        ...

    def find(self, query_filter: QueryFilter) -> Query:
        self.filter &= query_filter
        return self

    def sort(self, *sorts: TField) -> Query:
        self.sort_by.extend(sorts)
        return self


class QueryResult(ABC, Generic[TModel]):
    @abstractmethod
    async def __aiter__(self):
        ...

    async def flatten(self) -> list[TModel]:
        return [model async for model in self]