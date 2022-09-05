from bevy import Inject, bevy_method
from starlette.responses import HTMLResponse
from typing import Any, Type

from wordlette.responses import Response
from wordlette.templates.engine import TemplateEngine


class Template(Response):
    def __init__(self, template: str, scope: dict[str, Any]):
        super().__init__()
        self.scope = scope
        self.template_name = template

    def add_to_scope(self, name: str, value: Any):
        self.scope[name] = value

    @bevy_method
    async def _create_response_instance(
        self, response_type: Type[HTMLResponse], templates: TemplateEngine = Inject
    ) -> HTMLResponse:
        template = await templates.get_template(self.template_name)
        return response_type(
            content=await template.render(self.scope),
            status_code=self.status_code,
            headers=self.headers,
        )
