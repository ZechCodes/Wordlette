from bevy import dependency, inject
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.app import WordletteApp
from wordlette.middlewares import Middleware
from wordlette.middlewares.state_router import StateRouterMiddleware, RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State, StateMachine


def test_empty_app():
    app = WordletteApp()
    response = TestClient(app).get("/")
    assert response.status_code == 500


def test_custom_middleware_extension():
    class TestMiddleware(Middleware):
        async def run(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"Hello, world!"})
            await self.next()

    app = WordletteApp(middleware=[TestMiddleware])
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


def test_app_with_state_router_and_routes():
    class Index(Route):
        path = "/"

        async def get(self, _: Request.Get):
            return PlainTextResponse("Hello, world!")

    class TestPage(Route):
        path = "/test"

        async def get(self, _: Request.Get):
            return PlainTextResponse("Test page get")

        async def post(self, _: Request.Post):
            return PlainTextResponse("Test page post")

    class SetupRouterState(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            route_manager.create_router(Index, TestPage)

    def create_router_middleware(call_next):
        return StateRouterMiddleware(
            call_next, statemachine=StateMachine(SetupRouterState)
        )

    app = WordletteApp(middleware=[create_router_middleware])
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"

    response = TestClient(app).get("/test")
    assert response.status_code == 200
    assert response.text == "Test page get"

    response = TestClient(app).post("/test")
    assert response.status_code == 200
    assert response.text == "Test page post"
