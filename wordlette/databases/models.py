from bevy import get_repository

import wordlette.databases.drivers as drivers
from wordlette.databases.query_ast import ASTGroupNode
from wordlette.databases.statuses import DatabaseStatus
from wordlette.models import Model
from wordlette.utils.contextual_methods import contextual_method


class DatabaseModel(Model):
    __models__ = set()

    def __init_subclass__(cls, **kwargs):
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

    @delete.classmethod
    async def delete(cls, *items: "DatabaseModel") -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.delete(cls, *items)

    @classmethod
    async def update(cls, *items: "DatabaseModel") -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.update(cls, *items)

    @classmethod
    async def get(cls, predicate: ASTGroupNode) -> DatabaseStatus:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.get(cls, predicate)
