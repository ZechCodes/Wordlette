from wordlette.cms.states.setup.enums import SetupCategory
from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.cms.themes import Template
from wordlette.requests import Request


class SetupComplete(SetupRoute, setup_category=SetupCategory.NoCategory):
    path = "/setup-complete"

    async def get_setup_page(self, _: Request.Get):
        return Template(
            "setup-complete.html",
            title="Wordlette",
            subtitle="Setup Complete",
        )
