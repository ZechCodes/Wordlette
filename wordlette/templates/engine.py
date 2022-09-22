from __future__ import annotations

from pathlib import Path

from wordlette.utilities.null_type import NullType
from wordlette.templates.renderers import TemplateRenderer
from typing import Generator


class TemplateEngine:
    def __init__(
        self,
        name: str,
        search_paths: list[Path],
        parent_engine: TemplateEngine | None = None,
    ):
        self.name = name
        self.parent = NullTemplateEngine() if parent_engine is None else parent_engine
        self.search_paths = search_paths

    async def get_template(self, relative_path: str) -> TemplateRenderer:
        return TemplateRenderer(relative_path, self.get_template_search_paths())

    def get_template_search_paths(self) -> Generator[None, Path, None]:
        yield from (
            path
            for search_path in self.parent.get_template_search_paths()
            if (path := search_path / self.name).exists()
        )
        yield from self.search_paths

    def __repr__(self):
        parent_simple_repr = (
            f"<{type(self.parent).__name__} {self.name} ...>" if self.parent else "NONE"
        )
        return f"<{type(self).__name__} {self.name!r}, parent={parent_simple_repr}, paths={self.search_paths}>"


class NullTemplateEngine(TemplateEngine, NullType):
    def __init__(self):
        super().__init__("NULL_TEMPLATE_ENGINE", [], self)

    async def get_template(self, *_) -> None:
        return None

    def get_template_search_paths(self, *_) -> Generator[None, None, None]:
        yield from []
