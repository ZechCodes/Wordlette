from bevy import dependency, inject
from starlette.responses import PlainTextResponse

from wordlette.middlewares.router_middleware import RouteManager
from wordlette.state_machines import State


class Serving(State):
    @inject
    def enter_state(self, router: RouteManager = dependency()) -> None:
        router.router.add_route("/", PlainTextResponse("Hello, world!"))
