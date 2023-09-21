from bevy import get_repository

from wordlette.databases.drivers import AbstractDatabaseDriver, DatabaseDriver
from wordlette.databases.settings_models import DatabaseSettings
from wordlette.databases.statuses import DatabaseStatus, DatabaseSuccessStatus
from wordlette.utils.dependency_injection import inject, AutoInject


class DatabaseController(AutoInject):
    def __init__(self):
        self._driver: AbstractDatabaseDriver | None = None

    @property
    def connected(self) -> bool:
        if self._driver is None:
            return False

        return self._driver.connected

    async def connect(
        self, db_settings: DatabaseSettings @ inject = None
    ) -> DatabaseStatus:
        driver = DatabaseDriver.__drivers__.get(db_settings.driver)
        if driver is None:
            raise RuntimeError(
                f"Could not find a driver that matches {db_settings.driver!r}"
            )

        self._driver = driver()
        get_repository().set(DatabaseDriver, self._driver)
        return await self._driver.connect()

    async def disconnect(self) -> DatabaseStatus:
        if self._driver is None:
            return DatabaseSuccessStatus(None)

        if status := await self._driver.disconnect():
            self._driver = None
            get_repository().set(AbstractDatabaseDriver, None)

        return status
