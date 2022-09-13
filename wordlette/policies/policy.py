from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, ParamSpec, TypeAlias, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

PolicyCollection: TypeAlias = set[Callable[P, Awaitable] | "Policy"]


class Policy(ABC):
    def __init__(self):
        self._policies = PolicyCollection()
        self._preempt_policies = PolicyCollection()

    async def __call__(self, *args: P.args, **kwargs: P.kwargs):
        await self.enforce(*args, **kwargs)

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def run(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        ...

    def add_policy(self, policy: Policy):
        self._add_policy(policy, self._policies)

    def add_preempting_policy(self, policy: Policy):
        self._add_policy(policy, self._preempt_policies)

        value = await self.run(value, *args, **kwargs)
    async def enforce(self, *args: P.args, **kwargs: P.kwargs):
        await self._run_policies(self._preempt_policies, *args, **kwargs)
        await self._run_policies(self._policies, *args, **kwargs)

    @staticmethod
    def _add_policy(policy: Policy, policy_collection: set[Policy]):
        policy_collection.add(policy)

    @staticmethod
    async def _run_policies(
        policies: PolicyCollection, *args: P.args, **kwargs: P.kwargs
    ):
        for policy in policies:
            await policy(*args, **kwargs)
