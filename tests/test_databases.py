from typing import Type

import pytest
from bevy import get_repository, Repository

from wordlette.configs.managers import ConfigManager
from wordlette.databases.drivers import DatabaseDriver
from wordlette.databases.models import DatabaseModel
from wordlette.databases.predicates import DatabasePredicate
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

    async def get(self, *predicates: DatabasePredicate) -> DatabaseStatus:
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
