from typing import Type

from wordlette.utilities.null_type import NullType
from .state import State


class NullState(NullType, State):
    name = "Null"

    async def enter_state(self):
        pass

    async def next_state(self) -> Type[State]:
        pass
