from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ParamSpec, TypeAlias, TypeVar

P = ParamSpec("P")
PolicyCollection: TypeAlias = set["Policy"]
T = TypeVar("T")


class Policy(ABC):
    def __init__(self):
        self._policies = PolicyCollection()
        self._preempt_policies = PolicyCollection()

    async def __call__(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        return await self.enforce(value, *args, **kwargs)

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

    async def enforce(self, value: T, *args: P.args, **kwargs: P.kwargs) -> T:
        value = await self._run_policies(self._preempt_policies, value, *args, **kwargs)
        value = await self.run(value, *args, **kwargs)
        value = await self._run_policies(value, self._policies, *args, **kwargs)
        return value

    @staticmethod
    def _add_policy(policy: Policy, policy_collection: set[Policy]):
        policy_collection.add(policy)

    @staticmethod
    async def _run_policies(
        policies: PolicyCollection, value: T, *args: P.args, **kwargs: P.kwargs
    ) -> T:
        for policy in policies:
            value = await policy(value, *args, **kwargs)

        return value
