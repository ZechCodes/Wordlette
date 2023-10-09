from typing import overload

from wordlette.dbom.statuses import (
    DatabaseStatus,
)
from wordlette.models import Auto
from wordlette.users.accessors import UserAccessor
from wordlette.users.models import User


class UserRegistry:
    @overload
    def get(self, user_id: int) -> UserAccessor:
        ...

    @overload
    def get(self, user: User) -> UserAccessor:
        ...

    def get(self, user: int | User) -> UserAccessor:
        match user:
            case int():
                user_id = user

            case User():
                user_id = user.id

            case _:
                raise TypeError(f"Expected {int | User}, got {type(user)}")

        return UserAccessor(user_id)

    async def add(self, user: User) -> DatabaseStatus:
        if isinstance(user.id, Auto):
            return await User.add(user)

        return await user.sync()
