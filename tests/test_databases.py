from datetime import datetime
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
from wordlette.models import Auto
from wordlette.utils.at_annotateds import AtProvider


class DummyDriver(DatabaseDriver, driver_name="dummy"):
    def __init__(self):
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    async def add(self, *items: DatabaseModel) -> DatabaseStatus:
        pass

    async def count(
        *predicates: ASTGroupNode | Type[DatabaseModel],
    ) -> DatabaseStatus[int]:
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
    get_repository().set(DatabaseDriver, driver)
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
    assert result.value == [TestModel(id=10, string="test")]


@pytest.mark.asyncio
async def test_sqlite_driver_delete(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_delete"),
        TestModel(id=2, string="test_delete"),
        TestModel(id=3, string="test_delete"),
    )
    assert await sqlite_driver.delete(TestModel(id=1), TestModel(id=2))

    result = await sqlite_driver.fetch(when(TestModel.string == "test_delete"))
    assert len(result.value) == 1


@pytest.mark.asyncio
async def test_sqlite_driver_update(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_update"),
        TestModel(id=2, string="test_update"),
        TestModel(id=3, string="test_update"),
    )
    result = await sqlite_driver.update(TestModel(id=1, string="updated"))
    assert isinstance(result, DatabaseSuccessStatus)

    match await sqlite_driver.fetch(when(TestModel.string == "updated")):
        case DatabaseSuccessStatus([result]):
            assert result == TestModel(id=1, string="updated")

        case result:
            assert len(result.value) == 1


@pytest.mark.asyncio
async def test_sqlite_driver_auto_fields():
    class TestModel(DatabaseModel):
        id: int | Auto @ Property
        dt: datetime | Auto @ Property
        value: str @ Property

    driver = SQLiteDriver()
    config = SQLiteConfig(filename=":memory:")
    assert await driver.connect(config)
    assert await driver.sync_schema({TestModel})

    get_repository().set(DatabaseDriver, driver)

    a, b = TestModel(value="test"), TestModel(value="test")
    assert await driver.add(a, b)
    assert isinstance(a.id, int)
    assert isinstance(b.id, int)
    assert a.id != b.id

    assert (result := await driver.fetch(when(TestModel.id == a.id)))
    assert result.value[0].id == a.id


@pytest.mark.asyncio
async def test_sqlite_select_all(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_select_all"),
        TestModel(id=2, string="test_select_all"),
        TestModel(id=3, string="test_select_all"),
    )
    result = await sqlite_driver.fetch(TestModel)
    assert result.value == [
        TestModel(id=1, string="test_select_all"),
        TestModel(id=2, string="test_select_all"),
        TestModel(id=3, string="test_select_all"),
    ]


@pytest.mark.asyncio
async def test_sqlite_select_limit(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_limit"),
        TestModel(id=2, string="test_limit"),
        TestModel(id=3, string="test_limit"),
        TestModel(id=4, string="test_limit"),
        TestModel(id=5, string="test_limit"),
        TestModel(id=6, string="test_limit"),
    )

    result = await sqlite_driver.fetch(when(TestModel).limit(2))
    assert result.value == [
        TestModel(id=1, string="test_limit"),
        TestModel(id=2, string="test_limit"),
    ]

    result = await sqlite_driver.fetch(when(TestModel).limit(2, 1))
    assert result.value == [
        TestModel(id=3, string="test_limit"),
        TestModel(id=4, string="test_limit"),
    ]

    result = await sqlite_driver.fetch(when(TestModel).limit(2, 2))
    assert result.value == [
        TestModel(id=5, string="test_limit"),
        TestModel(id=6, string="test_limit"),
    ]


@pytest.mark.asyncio
async def test_sqlite_select_ordered(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="a"),
        TestModel(id=2, string="b"),
        TestModel(id=3, string="c"),
        TestModel(id=4, string="c"),
        TestModel(id=5, string="b"),
        TestModel(id=6, string="a"),
    )
    result = await sqlite_driver.fetch(
        when(TestModel).sort(TestModel.string.desc, TestModel.id)
    )
    assert result.value == [
        TestModel(id=3, string="c"),
        TestModel(id=4, string="c"),
        TestModel(id=2, string="b"),
        TestModel(id=5, string="b"),
        TestModel(id=1, string="a"),
        TestModel(id=6, string="a"),
    ]


@pytest.mark.asyncio
async def test_sqlite_count(sqlite_driver: SQLiteDriver):
    await sqlite_driver.add(
        TestModel(id=1, string="test_count"),
        TestModel(id=2, string="test_count_2"),
        TestModel(id=3, string="test_count_2"),
    )

    result = await sqlite_driver.count(when(TestModel))
    assert result.value == 3

    result = await sqlite_driver.count(when(TestModel.string == "test_count_2"))
    assert result.value == 2
