import mako.template
from pathlib import Path
from typing import Any


class TemplateRenderer:
    def __init__(self, template_path: Path):
        self.template_path = template_path

    async def render(self, scope: dict[str, Any]) -> str:
        return mako.template.Template(filename=str(self.template_path)).render(**scope)
