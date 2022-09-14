from __future__ import annotations

from abc import abstractmethod
from typing import Awaitable, Callable, Generic, ParamSpec, TypeAlias, TypeVar

from .policy import Policy

P = ParamSpec("P")
T = TypeVar("T")

PolicyCollection: TypeAlias = set[Callable[P, Awaitable[T]] | "ValuePolicy[T]"]


class ValuePolicy(Generic[T], Policy):
    async def __call__(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        return await self.enforce(*args, **kwargs)

    @abstractmethod
    async def rule(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        ...

    async def enforce(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        value = await self._run_policies(self._preempt_policies, value, *args, **kwargs)
        value = await self._run_policies(self._policies, value, *args, **kwargs)
        return value

    @staticmethod
    async def _run_policies(
        policies: PolicyCollection, value: T, *args: P.args, **kwargs: P.kwargs
    ) -> T:
        for policy in policies:
            value = await policy(value, *args, **kwargs)

        return value
