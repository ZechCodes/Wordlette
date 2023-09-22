from typing import Type

import pytest
from bevy import get_repository, Repository

from wordlette.configs.managers import ConfigManager
from wordlette.databases.drivers import DatabaseDriver
from wordlette.databases.models import DatabaseModel
from wordlette.databases.properties import Property
from wordlette.databases.query_ast import (
    ASTComparisonNode,
    ASTGroupNode,
    ASTLiteralNode,
    ASTReferenceNode,
    LogicalOperator,
    Operator,
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

    async def get(self, *predicates: ASTGroupNode) -> DatabaseStatus:
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


@pytest.mark.asyncio
async def test_connect():
    from wordlette.databases.controllers import DatabaseController

    controller = DatabaseController()
    assert not controller.connected

    status = await controller.connect()
    assert status == DatabaseSuccessStatus(None)
    assert controller.connected
    assert isinstance(get_repository().get(DatabaseDriver), DummyDriver)


def test_predicates():
    ast = (
        when(10 > ASTReferenceNode("x") > 5)
        .And(when(ASTReferenceNode("y") < 10).Or(ASTReferenceNode("y") > 20))
        .Or(ASTReferenceNode("z") > 10)
    )

    assert ast == ASTGroupNode(
        [
            ASTComparisonNode(
                ASTReferenceNode("x"), ASTLiteralNode(10), Operator.LESS_THAN
            ),
            LogicalOperator.AND,
            ASTComparisonNode(
                ASTReferenceNode("x"), ASTLiteralNode(5), Operator.GREATER_THAN
            ),
            LogicalOperator.AND,
            ASTGroupNode(
                [
                    ASTComparisonNode(
                        ASTReferenceNode("y"), ASTLiteralNode(10), Operator.LESS_THAN
                    ),
                    LogicalOperator.OR,
                    ASTComparisonNode(
                        ASTReferenceNode("y"), ASTLiteralNode(20), Operator.GREATER_THAN
                    ),
                ]
            ),
            LogicalOperator.OR,
            ASTComparisonNode(
                ASTReferenceNode("z"), ASTLiteralNode(10), Operator.GREATER_THAN
            ),
        ]
    )

    ast = when(ASTReferenceNode("x") == 10, ASTReferenceNode("y") == 20)
    assert ast == ASTGroupNode(
        [
            ASTComparisonNode(
                ASTReferenceNode("x"), ASTLiteralNode(10), Operator.EQUALS
            ),
            LogicalOperator.AND,
            ASTComparisonNode(
                ASTReferenceNode("y"), ASTLiteralNode(20), Operator.EQUALS
            ),
        ]
    )


def test_model_fields():
    class TestModel(DatabaseModel):
        field: str @ Property()

    assert isinstance(TestModel.field, ASTReferenceNode)
    assert TestModel.field.field == TestModel.__fields__["field"]
