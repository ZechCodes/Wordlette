from typing import Type

from bevy import bevy_method, Inject
from wordlette import Logging
from wordlette.databases import Database, Model
from wordlette.databases.databases import TModel
from wordlette.databases.filters import QueryFilter
from wordlette.databases.query import Query


class SQLAlchemyDatabaseDriver(Database):
    async def add(self, model: TModel):
        pass

    @bevy_method
    async def connect(self, log: Logging = Inject):
        log.info("Connecting to database using SQLAlchemy")

    async def get(self, model: Model):
        ...

    def query(self, model: Type[TModel], query_filter: QueryFilter) -> Query[TModel]:
        pass
