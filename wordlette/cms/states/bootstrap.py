from bevy import dependency, inject
from starlette.responses import PlainTextResponse

from wordlette.cms import CMSApp
from wordlette.state_machines import State


class BootstrapState(State):
    @inject
    async def enter_state(self, app: CMSApp = dependency()):
        app.set_router(self._bootstrap_error_app)
        return self.cycle()

    async def _bootstrap_error_app(self, scope, receive, send):
        response = PlainTextResponse("The Wordlette CMS is starting.", status_code=200)
        await response(scope, receive, send)
