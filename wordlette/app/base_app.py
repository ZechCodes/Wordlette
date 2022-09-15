from abc import ABC, abstractmethod
from bevy import Context
from starlette.applications import Starlette
from starlette.types import Receive, Scope, Send
from typing import Iterator

from wordlette.events import Eventable
from wordlette.extensions.auto_loader import ExtensionInfo
from wordlette.state_machine import StateMachine


class BaseApp(ABC, Eventable):
    @classmethod
    @abstractmethod
    def start(cls, host: str, port: int, extensions_modules: Iterator[str]):
        ...

    @abstractmethod
    def load_app_extension(self, extension_info: ExtensionInfo):
        ...

    @abstractmethod
    def load_extension(self, extension_info: ExtensionInfo):
        ...

    @abstractmethod
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        ...

    @property
    @abstractmethod
    def app(self) -> Starlette | None:
        ...

    @property
    @abstractmethod
    def app_context(self) -> Context:
        ...

    @property
    @abstractmethod
    def context(self) -> Context:
        ...

    @property
    @abstractmethod
    def router(self) -> Starlette | None:
        ...

    @property
    @abstractmethod
    def state_machine(self) -> StateMachine:
        ...
