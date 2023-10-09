import pytest
from bevy import Repository

from wordlette.dbom import DatabaseDriver, SQLiteDriver
from wordlette.dbom.driver_sqlite import SQLiteConfig
from wordlette.dbom.models import DatabaseModel
from wordlette.users.models import User
from wordlette.users.registries import UserRegistry


@pytest.mark.asyncio
async def test_user_registry_add():
    repo = Repository.factory()
    Repository.set_repository(repo)

    repo.set(DatabaseDriver, driver := SQLiteDriver())

    assert await driver.connect(SQLiteConfig(filename=":memory:"))
    await driver.sync_schema(DatabaseModel.__models__)

    registry = UserRegistry()
    user = User(name="test")
    result = await registry.add(user)
    if not result:
        raise result.exception

    assert await registry.get(user.id) == user

    user.name = "test2"
    result = await registry.add(user)
    if not result:
        raise result.exception

    assert await registry.get(user.id).name == "test2"


@pytest.mark.asyncio
async def test_user_metadata_add():
    repo = Repository.factory()
    Repository.set_repository(repo)

    repo.set(DatabaseDriver, driver := SQLiteDriver())
    await driver.connect(SQLiteConfig(filename=":memory:"))
    await driver.sync_schema(DatabaseModel.__models__)

    registry = UserRegistry()
    user = User(name="test")
    await registry.add(user)

    await user.metadata.set(key="value")

    assert await registry.get(user.id).metadata["key"] == "value"

    assert (
        await registry.get(user.id).metadata.get("foobar", "default test")
        == "default test"
    )
