from bevy import inject, dependency
from starlette.responses import HTMLResponse

from wordlette.core import WordletteApp
from wordlette.middlewares.router_middleware import RouterMiddleware, RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import StateMachine, State


class Index(Route):
    path = "/"

    async def get(self, request: Request.Get):
        return HTMLResponse(
            """
            <h3>Hello, world!</h3>
            <form action="/hello">
                <input name="name" placeholder="Enter your name" />
                <button>Submit</button>
            </form>
            """
        )


class Hello(Route):
    path = "/hello/"

    async def get(self, request: Request.Get):
        return HTMLResponse(
            f"Hello {request.query_params['name']}!<br /><a href='/'>Home</a>"
        )


class ServingState(State):
    @inject
    async def enter_state(self, route_manager: RouteManager = dependency()):
        Route.register_routes(route_manager.router)


app = WordletteApp(
    middleware=[RouterMiddleware],
    state_machine=StateMachine(ServingState),
)
