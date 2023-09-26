from abc import ABC, abstractmethod
from typing import Type, TypeAlias, TypeVar, Callable, get_origin

from wordlette.configs import ConfigModel
from wordlette.databases.models import DatabaseModel
from wordlette.databases.properties import DatabaseProperty
from wordlette.databases.query_ast import ASTGroupNode
from wordlette.databases.settings_forms import DatabaseSettingsForm
from wordlette.databases.statuses import DatabaseStatus

DriverName: TypeAlias = str
DriverNiceName: TypeAlias = str
T = TypeVar("T")


class AbstractDatabaseDriver(ABC):
    __drivers__: "dict[DriverName, Type[AbstractDatabaseDriver]]"
    __settings_form__: Type[DatabaseSettingsForm]
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
    async def connect(self, config: ConfigModel | None = None) -> DatabaseStatus:
        ...

    @abstractmethod
    async def count(
        *predicates: ASTGroupNode | Type[DatabaseModel],
    ) -> DatabaseStatus[int]:
        ...

    @abstractmethod
    async def delete(self, *items: DatabaseModel) -> DatabaseStatus:
        ...

    @abstractmethod
    async def disconnect(self) -> DatabaseStatus:
        ...

    @abstractmethod
    async def fetch(
        self, *predicates: ASTGroupNode | Type[DatabaseModel]
    ) -> DatabaseStatus:
        ...

    @abstractmethod
    async def sync_schema(self, models: set[Type[DatabaseModel]]) -> DatabaseStatus:
        ...

    @abstractmethod
    async def update(self, *items: DatabaseModel) -> DatabaseStatus:
        ...


class DatabaseDriver(AbstractDatabaseDriver, ABC):
    __drivers__ = {}
    driver_name: DriverName
    nice_name: DriverNiceName
    auto_value_factories: dict[Type[T], Callable[[DatabaseModel], T]] = {}

    def __init_subclass__(cls, **kwargs):
        cls.driver_name = kwargs.pop(
            "driver_name", getattr(cls, "driver_name", cls.__name__)
        )
        cls.nice_name = kwargs.pop("nice_name", getattr(cls, "nice_name", cls.__name__))

        super().__init_subclass__(**kwargs)
        cls.add_driver(cls)

    @classmethod
    def add_driver(cls, driver: "Type[AbstractDatabaseDriver]"):
        cls.__drivers__[driver.driver_name] = driver

    @classmethod
    def disable_driver(cls, name: DriverName):
        cls.__drivers__.pop(name, None)

    def get_value_factory(
        self, field: DatabaseProperty
    ) -> Callable[[DatabaseModel], T] | None:
        field_type = get_origin(field.type) or field.type
        for factory_type, factory in self.auto_value_factories.items():
            if issubclass(field_type, factory_type):
                return factory

        return None
