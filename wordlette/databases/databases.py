from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from bevy import Bevy
from .query import Query, QueryFilter, QueryResult

TModel = TypeVar("TModel")


class Database(ABC, Bevy):
    @abstractmethod
    async def connect(self):
        ...

    @abstractmethod
    def query(self, model: Type[TModel], query_filter: QueryFilter) -> Query[TModel]:
        ...

    def __getitem__(self, model: Type[TModel]) -> Query[TModel]:
        return Query(model)

    async def delete(self, model: Type[TModel], query_filter: QueryFilter):
        query = self.query(model, query_filter)
        await query.delete()

    async def fetch_all(
        self, model: Type[TModel], query_filter: QueryFilter
    ) -> QueryResult[TModel]:
        query = self.query(model, query_filter)
        return await query.fetch_all()

    async def fetch_one(
        self, model: Type[TModel], query_filter: QueryFilter
    ) -> QueryResult[TModel]:
        query = self.query(model, query_filter)
        return await query.fetch_one()

    async def update(
        self, model: Type[TModel], query_filter: QueryFilter, **changes: Any
    ):
        query = self.query(model, query_filter)
        await query.update(**changes)
