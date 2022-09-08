from mako.lookup import TemplateLookup
from pathlib import Path
from typing import Any, Iterable


class TemplateRenderer:
    def __init__(self, template_file: str, template_paths: Iterable[Path]):
        self.template = TemplateLookup(
            directories=list(map(str, template_paths))
        ).get_template(template_file)

    async def render(self, scope: dict[str, Any]) -> str:
        return self.template.render(**scope)
