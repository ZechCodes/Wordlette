from typing import Type

from wordlette.databases import Database, Model
from wordlette.databases.databases import TModel
from wordlette.databases.filters import QueryFilter
from wordlette.databases.query import Query


class SQLAlchemyDatabaseDriver(Database):
    async def add(self, model: TModel):
        pass

    async def connect(self):
        print("Oh hi")

    async def get(self, model: Model):
        ...

    def query(self, model: Type[TModel], query_filter: QueryFilter) -> Query[TModel]:
        pass
