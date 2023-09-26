from starlette.responses import RedirectResponse

from wordlette.cms.states.setup.route_types import SetupRoute
from wordlette.requests import Request
from wordlette.state_machines import StateMachine
from wordlette.utils.dependency_injection import inject


class Launch(SetupRoute):
    path = "/launch"

    async def launch_site(self, _: Request.Get, statemachine: StateMachine @ inject):
        await statemachine.cycle()
        return RedirectResponse("/")
