from wordlette.cms.states.setup.enums import SetupCategory
from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.core.requests import Request


class Index(SetupRoute, setup_category=SetupCategory.Page):
    path = "/"

    async def get(self, request: Request.Get):
        next_page = await self.get_next_page()
        return Template(
            "index.html",
            title="Wordlette",
            subtitle="Setting Up Your Site",
            next_page_url=next_page.url(),
        )
