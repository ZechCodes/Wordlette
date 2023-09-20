from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.requests import Request


class Index(SetupRoute):
    path = "/"

    async def get(self, request: Request.Get):
        next_page = await self.get_next_page()
        return Template(
            "index.html",
            title="Wordlette",
            subtitle="Setting Up Your Site",
            next_page_url=next_page.url(),
        )
