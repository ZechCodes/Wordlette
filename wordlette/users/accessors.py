from typing import Any, Generator

import wordlette.users.models as models
from wordlette.dbom.statuses import (
    DatabaseExceptionStatus,
    DatabaseSuccessStatus,
)


class UserMetadataKeyAccessor:
    def __init__(self, user_id: int, key: str, default: str = None):
        self.user_id = user_id
        self.key = key
        self.default = default

    def __await__(self):
        return self.fetch().__await__()

    async def fetch(self):
        results = await models.UserMetadata.fetch(
            models.UserMetadata.user_id == self.user_id,
            models.UserMetadata.key == self.key,
        )
        match results:
            case DatabaseSuccessStatus([metadata]):
                return metadata.value

            case DatabaseSuccessStatus([]):
                return self.default

            case DatabaseExceptionStatus(exception):
                raise exception

    def set(self, value: str):
        return models.UserMetadata.add(
            models.UserMetadata(
                user_id=self.user_id,
                key=self.key,
                value=value,
            )
        )


class UserMetadataAccessor:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __getitem__(self, key: str) -> UserMetadataKeyAccessor:
        return UserMetadataKeyAccessor(self.user_id, key)

    def __await__(self):
        return self.fetch().__await__()

    def get(self, key: str, default: str | None = None):
        return UserMetadataKeyAccessor(self.user_id, key, default)

    async def set(self, **kwargs):
        for key, value in kwargs.items():
            result = await UserMetadataKeyAccessor(
                user_id=self.user_id,
                key=key,
            ).set(value)

            if not result:
                raise result.exception

    async def fetch(self) -> dict[str, str]:
        match await models.UserMetadata.fetch(
            models.UserMetadata.user_id == self.user_id
        ):
            case DatabaseSuccessStatus(metadata):
                return {item.key: item.value for item in metadata}

            case DatabaseExceptionStatus(exception):
                raise exception


class UserPropertyAccessor:
    def __init__(self, user_id: int, property_name: str):
        self.user_id = user_id
        self.property_name = property_name

    def __await__(self):
        return self.fetch().__await__()

    async def fetch(self) -> Any:
        match await models.User.fetch(models.User.id == self.user_id):
            case DatabaseSuccessStatus([user]):
                return getattr(user, self.property_name)

            case DatabaseExceptionStatus(exception):
                raise exception


class UserAccessor:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __await__(self) -> "Generator[Any, None, models.User]":
        return self.fetch().__await__()

    def __getattr__(self, item):
        if hasattr(models.User, item):
            return UserPropertyAccessor(self.user_id, item)

        return NotImplemented

    @property
    def metadata(self) -> UserMetadataAccessor:
        return UserMetadataAccessor(self.user_id)

    async def fetch(self) -> "models.User":
        match await models.User.fetch(models.User.id == self.user_id):
            case DatabaseSuccessStatus([user]):
                return user

            case DatabaseExceptionStatus(exception):
                raise exception
