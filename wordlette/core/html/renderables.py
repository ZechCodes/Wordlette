from typing import runtime_checkable, Protocol

from markupsafe import Markup


@runtime_checkable
class Renderable(Protocol):
    def render(self) -> Markup:
        ...
