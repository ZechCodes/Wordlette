from bevy import get_repository

import wordlette.databases.drivers as drivers
from wordlette.databases.query_ast import ASTGroupNode
from wordlette.databases.statuses import DatabaseStatus
from wordlette.models import Model
from wordlette.utils.contextual_methods import contextual_method


class DatabaseModel(Model):
    __models__ = set()
    __model_name__: str

    def __init_subclass__(cls, **kwargs):
        cls.__model_name__ = kwargs.pop(
            "name", getattr(cls, "__model_name__", cls.__name__)
        )
        super().__init_subclass__(**kwargs)
        DatabaseModel.__models__.add(cls)

    async def sync(self) -> DatabaseStatus:
        return await type(self).update(self)

    @contextual_method
    async def delete(self) -> DatabaseStatus:
        return await type(self).delete(self)

    @classmethod
    async def add(cls, *items: "DatabaseModel") -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.add(cls, *items)

    @classmethod
    async def fetch(cls, predicate: ASTGroupNode) -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.fetch(cls, predicate)

    @delete.classmethod
    async def delete(cls, *items: "DatabaseModel") -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.delete(cls, *items)

    @classmethod
    async def update(cls, *items: "DatabaseModel") -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.update(cls, *items)
