from abc import ABC, abstractmethod
from typing import Any


class AbstractSessionStore(ABC):
    @abstractmethod
    def generate_session_id(self) -> str:
        ...

    @abstractmethod
    def get(self, session_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    def set(self, session_id: str, session: dict[str, Any]):
        ...
