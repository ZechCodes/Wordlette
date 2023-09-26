from typing import Callable, TypeVar, Any, Generator

from bevy import get_repository

import wordlette.databases.drivers as drivers
from wordlette.databases.properties import DatabaseProperty
from wordlette.databases.query_ast import ASTComparisonNode
from wordlette.databases.statuses import DatabaseStatus
from wordlette.models import Model
from wordlette.utils.contextual_methods import contextual_method

T = TypeVar("T")


class DatabaseModel(Model):
    __fields__: dict[str, DatabaseProperty]
    __models__ = set()
    __model_name__: str

    def __init_subclass__(cls, **kwargs):
        cls.__model_name__ = kwargs.pop(
            "name", getattr(cls, "__model_name__", cls.__name__)
        )
        super().__init_subclass__(**kwargs)
        DatabaseModel.__models__.add(cls)

    def __get_auto_value__(self, field: DatabaseProperty) -> Callable[[], T]:
        driver = get_repository().get(drivers.DatabaseDriver)
        if factory := driver.get_value_factory(field):
            return factory

        return super().__get_auto_value__(field)

    async def sync(self) -> "DatabaseStatus[drivers.DatabaseDriver]":
        return await type(self).update(self)

    @contextual_method
    async def delete(self) -> "DatabaseStatus[drivers.DatabaseDriver]":
        return await type(self).delete(self)

    @classmethod
    async def add(
        cls, *items: "DatabaseModel"
    ) -> "DatabaseStatus[drivers.DatabaseDriver]":
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.add(cls, *items)

    @classmethod
    async def count(
        cls, *predicates: "ASTGroupNode | DatabaseModel | bool", columns: Any = None
    ) -> DatabaseStatus[int]:
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.count(
            cls, *predicates, *cls._build_colum_predicates(columns)
        )

    @classmethod
    async def fetch(
        cls, *predicates: "ASTGroupNode | DatabaseModel | bool", **columns: Any
    ) -> "DatabaseStatus[list[DatabaseModel]]":
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.fetch(
            cls, *predicates, *cls._build_colum_predicates(columns)
        )

    @delete.classmethod
    async def delete(
        cls, *items: "DatabaseModel"
    ) -> "DatabaseStatus[drivers.DatabaseDriver]":
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.delete(cls, *items)

    @classmethod
    async def update(
        cls, *items: "DatabaseModel"
    ) -> "DatabaseStatus[drivers.DatabaseDriver]":
        driver = get_repository().get(drivers.DatabaseDriver)
        return await driver.update(cls, *items)

    @classmethod
    def _build_colum_predicates(
        cls, columns: dict[str, Any]
    ) -> Generator[ASTComparisonNode | bool, None, None]:
        for name, value in columns.items():
            if name not in cls.__fields__:
                raise ValueError(f"Invalid column {name!r} for model {cls.__name__}")

            yield getattr(cls, name) == value
