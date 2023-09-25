from typing import Type

import pytest
import pytest_asyncio
from bevy import get_repository, Repository

from wordlette.configs.managers import ConfigManager
from wordlette.databases.driver_sqlite import SQLiteDriver, SQLiteConfig
from wordlette.databases.drivers import DatabaseDriver
from wordlette.databases.models import DatabaseModel
from wordlette.databases.properties import Property
from wordlette.databases.query_ast import (
    ASTComparisonNode,
    ASTGroupNode,
    ASTLiteralNode,
    ASTReferenceNode,
    ASTLogicalOperatorNode,
    ASTOperatorNode,
    when,
)
from wordlette.databases.statuses import DatabaseSuccessStatus, DatabaseStatus
from wordlette.utils.at_annotateds import AtProvider


class DummyDriver(DatabaseDriver, driver_name="dummy"):
    def __init__(self):
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def add(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    async def fetch(self, *predicates: ASTGroupNode) -> DatabaseStatus:
        pass

    async def delete(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    async def sync_schema(self, models: set[Type[DatabaseModel]]) -> DatabaseStatus:
        pass

    async def update(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    async def connect(self) -> DatabaseSuccessStatus:
        self._connected = True
        return DatabaseSuccessStatus(None)

    async def disconnect(self) -> DatabaseSuccessStatus:
        self._connected = False
        return DatabaseSuccessStatus(None)


class DummyConfigManager(ConfigManager):
    def __init__(self):
        super().__init__()
        self._config = {
            "database": {
                "driver": "dummy",
            }
        }


@pytest.fixture(scope="function", autouse=True)
def reset_bevy_repository():
    repo = Repository.factory()
    repo.add_providers(AtProvider())
    repo.set(ConfigManager, DummyConfigManager())
    Repository.set_repository(repo)


@pytest.fixture(scope="function", autouse=True)
def reset_database_models():
    DatabaseModel.__models__.clear()


class TestModel(DatabaseModel):
    id: int @ Property()
    string: str | None @ Property()


@pytest_asyncio.fixture()
async def sqlite_driver():
    driver = SQLiteDriver()
    config = SQLiteConfig(filename=":memory:")
    await driver.connect(config)
    await driver.sync_schema({TestModel})
    return driver


@pytest.mark.asyncio
async def test_connect():
    from wordlette.databases.controllers import DatabaseController

    controller = DatabaseController()
    assert not controller.connected

    status = await controller.connect()
    assert status == DatabaseSuccessStatus(None)
    assert controller.connected
    assert isinstance(get_repository().get(DatabaseDriver), DummyDriver)


def test_query_ast():
    ast = (
        when(10 > ASTReferenceNode("x", None) > 5)
        .And(
            when(ASTReferenceNode("y", None) < 10).Or(ASTReferenceNode("y", None) > 20)
        )
        .Or(ASTReferenceNode("z", None) > 10)
    )

    assert ast == ASTGroupNode(
        [
            ASTComparisonNode(
                ASTReferenceNode("x", None),
                ASTLiteralNode(10),
                ASTOperatorNode.LESS_THAN,
            ),
            ASTLogicalOperatorNode.AND,
            ASTComparisonNode(
                ASTReferenceNode("x", None),
                ASTLiteralNode(5),
                ASTOperatorNode.GREATER_THAN,
            ),
            ASTLogicalOperatorNode.AND,
            ASTGroupNode(
                [
                    ASTComparisonNode(
                        ASTReferenceNode("y", None),
                        ASTLiteralNode(10),
                        ASTOperatorNode.LESS_THAN,
                    ),
                    ASTLogicalOperatorNode.OR,
                    ASTComparisonNode(
                        ASTReferenceNode("y", None),
                        ASTLiteralNode(20),
                        ASTOperatorNode.GREATER_THAN,
                    ),
                ]
            ),
            ASTLogicalOperatorNode.OR,
            ASTComparisonNode(
                ASTReferenceNode("z", None),
                ASTLiteralNode(10),
                ASTOperatorNode.GREATER_THAN,
            ),
        ]
    )

    ast = when(ASTReferenceNode("x", None) == 10, ASTReferenceNode("y", None) == 20)
    assert ast == ASTGroupNode(
        [
            ASTComparisonNode(
                ASTReferenceNode("x", None), ASTLiteralNode(10), ASTOperatorNode.EQUALS
            ),
            ASTLogicalOperatorNode.AND,
            ASTComparisonNode(
                ASTReferenceNode("y", None), ASTLiteralNode(20), ASTOperatorNode.EQUALS
            ),
        ]
    )


def test_model_fields():
    class TestModel(DatabaseModel):
        field: str @ Property()

    assert isinstance(TestModel.field, ASTReferenceNode)
    assert TestModel.field.field == TestModel.__fields__["field"]


def test_model_field_query_ast():
    class TestModel(DatabaseModel):
        field_a: str @ Property()
        field_b: int @ Property()

    ast = when(TestModel.field_a == "test", TestModel.field_b < 10)
    assert ast == ASTGroupNode(
        [
            ASTComparisonNode(
                ASTReferenceNode(TestModel.__fields__["field_a"], TestModel),
                ASTLiteralNode("test"),
                ASTOperatorNode.EQUALS,
            ),
            ASTLogicalOperatorNode.AND,
            ASTComparisonNode(
                ASTReferenceNode(TestModel.__fields__["field_b"], TestModel),
                ASTLiteralNode(10),
                ASTOperatorNode.LESS_THAN,
            ),
        ]
    )


@pytest.mark.asyncio
async def test_sqlite_driver_connects(sqlite_driver: SQLiteDriver):
    assert sqlite_driver.connected


@pytest.mark.asyncio
async def test_sqlite_driver_disconnects(sqlite_driver: SQLiteDriver):
    await sqlite_driver.disconnect()
    assert not sqlite_driver.connected


@pytest.mark.asyncio
async def test_sqlite_driver_add(sqlite_driver: SQLiteDriver):
    status = await sqlite_driver.add(TestModel(id=10, string="test"))
    assert isinstance(status, DatabaseSuccessStatus)


@pytest.mark.asyncio
async def test_sqlite_driver_fetch(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(TestModel(id=10, string="test"))
    result = await sqlite_driver.fetch(when(TestModel.string == "test"))
    assert isinstance(result, DatabaseSuccessStatus)
    assert result.result == [TestModel(id=10, string="test")]


@pytest.mark.asyncio
async def test_sqlite_driver_delete(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_delete"),
        TestModel(id=2, string="test_delete"),
        TestModel(id=3, string="test_delete"),
    )
    result = await sqlite_driver.delete(
        TestModel(id=1), TestModel(id=2), TestModel(id=3)
    )
    assert isinstance(result, DatabaseSuccessStatus)
    result = await sqlite_driver.fetch(when(TestModel.string == "test_delete"))
    assert isinstance(result, DatabaseSuccessStatus)
    assert len(result.result) == 0
