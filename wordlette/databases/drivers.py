from abc import ABC, abstractmethod
from typing import Type, TypeAlias

from wordlette.databases.models import DatabaseModel
from wordlette.databases.predicates import DatabasePredicate
from wordlette.databases.statuses import DatabaseStatus

DriverName: TypeAlias = str


class AbstractDatabaseDriver(ABC):
    __drivers__: "dict[DriverName, Type[AbstractDatabaseDriver]]"
    driver_name: DriverName

    @classmethod
    @abstractmethod
    def add_driver(cls, driver: "Type[AbstractDatabaseDriver]"):
        ...

    @classmethod
    @abstractmethod
    def disable_driver(cls, name: DriverName):
        ...

    @property
    @abstractmethod
    def connected(self) -> bool:
        ...

    @abstractmethod
    async def add(self, *items: DatabaseModel) -> DatabaseStatus:
        ...

    @abstractmethod
    async def connect(self) -> DatabaseStatus:
        ...

    @abstractmethod
    async def count(self, *predicates: DatabasePredicate) -> int:
        ...

    @abstractmethod
    async def disconnect(self) -> DatabaseStatus:
        ...

    @abstractmethod
    async def filter(self, *predicates: DatabasePredicate) -> DatabaseStatus:
        ...

    @abstractmethod
    async def get(self, *predicates: DatabasePredicate) -> DatabaseStatus:
        ...

    @abstractmethod
    async def remove(self, *items: DatabaseModel) -> DatabaseStatus:
        ...

    @abstractmethod
    async def sync_schema(self, models: set[Type[DatabaseModel]]) -> DatabaseStatus:
        ...

    @abstractmethod
    async def update(self, *items: DatabaseModel) -> DatabaseStatus:
        ...


class DatabaseDriver(ABC, AbstractDatabaseDriver):
    __drivers__ = {}
    driver_name: DriverName

    def __init_subclass__(cls, **kwargs):
        cls.driver_name = kwargs.pop(
            "driver_name", getattr(cls, "driver_name", cls.__name__)
        )

        super().__init_subclass__(**kwargs)
        cls.add_driver(cls)

    @classmethod
    def add_driver(cls, driver: "Type[AbstractDatabaseDriver]"):
        cls.__drivers__[driver.driver_name] = driver

    @classmethod
    def disable_driver(cls, name: DriverName):
        cls.__drivers__.pop(name, None)
