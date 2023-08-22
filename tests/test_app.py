import pytest
from bevy import dependency, inject, get_repository
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.core import WordletteApp
from wordlette.extensions import Extension
from wordlette.middlewares import Middleware
from wordlette.middlewares.router_middleware import RouteManager, RouterMiddleware
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.state_machines import State, StateMachine


def test_empty_app():
    class TestMiddleware(Middleware):
        def run(self, scope, receive, send):
            return self.next()

    class TestState(State):
        async def enter_state(self):
            return

    app = WordletteApp(
        middleware=[TestMiddleware], state_machine=StateMachine(TestState)
    )
    response = TestClient(app).get("/")
    assert response.status_code == 500


def test_custom_middleware():
    class TestMiddleware(Middleware):
        async def run(self, scope, receive, send):
            await PlainTextResponse("Hello, world!")(scope, receive, send)
            await self.next()

    class Starting(State):
        async def enter_state(self):
            return

    app = WordletteApp(
        middleware=[TestMiddleware], state_machine=StateMachine(Starting)
    )
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Hello, world!"


def test_custom_extension():
    class TestExtension(Extension):
        def __init__(self):
            self.test = "test"

    class Starting(State):
        async def enter_state(self):
            return

    _ = WordletteApp(
        extensions=[TestExtension], middleware=[], state_machine=StateMachine(Starting)
    )
    assert get_repository().find(TestExtension).value.test == "test"


def test_app_with_router_and_routes():
    class TestRoute(Route):
        class __metadata__:
            abstract = True
            registry = set()

    class Index(TestRoute):
        path = "/"

        async def get(self, _: Request.Get):
            return PlainTextResponse("Hello, world!")

    class TestPage(TestRoute):
        path = "/test"

        async def get(self, _: Request.Get):
            return PlainTextResponse("Test page get")

        async def post(self, _: Request.Post):
            return PlainTextResponse("Test page post")

    class TestState(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            TestRoute.register_routes(route_manager.router)

    app = WordletteApp(
        middleware=[RouterMiddleware], state_machine=StateMachine(TestState)
    )
    get_repository().get(RouteManager).create_router(Index, TestPage)

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
async def test_app_states_cycle():
    class RouteA(Route):
        path = "/a"

        async def get(self, _: Request.Get):
            return PlainTextResponse("RouteA")

    class RouteB(Route):
        path = "/b"

        async def get(self, _: Request.Get):
            return PlainTextResponse("RouteB")

    class StateA(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            route_manager.create_router(RouteA)

    class StateB(State):
        @inject
        async def enter_state(self, route_manager: RouteManager = dependency()):
            route_manager.create_router(RouteB)

    statemachine = StateMachine(StateA.goes_to(StateB))

    app = WordletteApp(middleware=[RouterMiddleware], state_machine=statemachine)
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
