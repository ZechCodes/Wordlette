import pytest
from bevy import dependency, inject, get_repository
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.app import WordletteApp
from wordlette.extensions import Extension
from wordlette.middlewares import Middleware
from wordlette.middlewares.state_router import StateRouterMiddleware, RouteManager
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State, StateMachine


def test_empty_app():
    app = WordletteApp()
    response = TestClient(app).get("/")
    assert response.status_code == 500


def test_custom_middleware():
    class TestMiddleware(Middleware):
        async def run(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 200})
            await send({"type": "http.response.body", "body": b"Hello, world!"})
            await self.next()

    app = WordletteApp(middleware=[TestMiddleware])
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


def test_custom_extension():
    class TestExtension(Extension):
        def __init__(self):
            self.test = "test"

    _ = WordletteApp(extensions=[TestExtension])
    assert get_repository().find(TestExtension).value.test == "test"


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


@pytest.mark.asyncio
async def test_app_router_states_cycle():
    class RouteA(Route):
        path = "/a"

        async def get(self, _: Request.Get):
            return PlainTextResponse("RouteA")

    class RouteB(Route):
        path = "/b"

        async def get(self, _: Request.Get):
            return PlainTextResponse("RouteB")

    class RouterStateA(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            route_manager.create_router(RouteA)

    class RouterStateB(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            route_manager.create_router(RouteB)

    statemachine = StateMachine(RouterStateA.goes_to(RouterStateB))

    def create_router_middleware(call_next):
        return StateRouterMiddleware(call_next, statemachine=statemachine)

    app = WordletteApp(middleware=[create_router_middleware])
    response = TestClient(app).get("/a")
    assert response.status_code == 200
    assert response.text == "RouteA"

    response = TestClient(app).get("/b")
    assert response.status_code == 404
    assert response.text == "Not Found"

    await statemachine.cycle()

    response = TestClient(app).get("/a")
    assert response.status_code == 404
    assert response.text == "Not Found"

    response = TestClient(app).get("/b")
    assert response.status_code == 200
    assert response.text == "RouteB"
