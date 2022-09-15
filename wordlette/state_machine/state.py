from __future__ import annotations

from abc import ABC, abstractmethod
from bevy import Bevy
from typing import Type


class State(ABC, Bevy):
    @property
    def name(self) -> str:
        return type(self).__name__

    @abstractmethod
    async def enter(self):
        """Run once the state has been transitioned to. This should return True if it should immediately advance to the
        next state."""

    @abstractmethod
    async def next(self) -> Type[State]:
        """Run when the state is being transitioned away from. This should return the type of state that should be
        transitioned to next."""
