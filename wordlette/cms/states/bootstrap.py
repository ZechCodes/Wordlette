from starlette.responses import PlainTextResponse

from wordlette.states import State


class BootstrapState(State):
    async def enter_state(self):
        self.value = self._bootstrap_error_app
        return True

    async def _bootstrap_error_app(self, scope, receive, send):
        response = PlainTextResponse("The Wordlette CMS is starting.", status_code=200)
        await response(scope, receive, send)
