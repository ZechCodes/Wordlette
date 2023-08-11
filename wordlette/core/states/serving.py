from dataclasses import dataclass

from bevy import dependency, inject
from starlette.responses import PlainTextResponse

from wordlette.configs import ConfigModel
from wordlette.middlewares.router_middleware import RouteManager
from wordlette.state_machines import State


@dataclass
class DemoConfig(ConfigModel):
    __config_key__ = "demo"

    message: str


class Serving(State):
    @inject
    def enter_state(
        self, router: RouteManager = dependency(), config: DemoConfig = dependency()
    ) -> None:
        router.router.add_route("/", PlainTextResponse(config.message))
