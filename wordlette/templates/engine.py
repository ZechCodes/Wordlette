from __future__ import annotations

from pathlib import Path

from wordlette.null_type import NullType
from wordlette.templates.renderers import TemplateRenderer


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
        return TemplateRenderer(await self.find_template_file(relative_path))

    async def find_template_file(self, relative_path: str):
        clean_path = relative_path.lstrip(r"\/")
        if template_file := await self.parent.find_template_file(
            f"{self.name}/{clean_path}"
        ):
            return template_file

        for search_path in self.search_paths:
            path = search_path / clean_path
            print("CHECKING", path)
            if path.exists():
                return path

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

    async def find_template_file(self, *_) -> None:
        return None
