from wordlette.pages import Page
from wordlette.responses import Response
from wordlette.templates import Template


class Index(Page):
    path = "/"

    async def response(self) -> Response:
        return Template("index.html", {"name": "World"})
