import pytest
from bevy import get_repository
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.app.app import StartupEvent
from wordlette.events import EventManager
from wordlette.middlewares.state_router import StateRouterMiddleware, RouteManager
from wordlette.state_machines import StateMachine, State


@pytest.mark.asyncio
async def test_router_is_set():
    repo = get_repository()
    repo.set(RouteManager, router := RouteManager())
    repo.set(EventManager, events := EventManager())

    class TestState(State):
        async def enter_state(self):
            router.router = PlainTextResponse("Test", status_code=200)

    async def dummy(*args, **kwargs):
        ...

    app = StateRouterMiddleware(dummy, statemachine=StateMachine(TestState))
    await events.emit(StartupEvent())
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Test"


@pytest.mark.asyncio
async def test_router_cycle():
    repo = get_repository()
    repo.set(RouteManager, router := RouteManager())
    repo.set(EventManager, events := EventManager())

    class TestStateA(State):
        async def enter_state(self):
            router.router = PlainTextResponse("TestA", status_code=200)

    class TestStateB(State):
        async def enter_state(self):
            router.router = PlainTextResponse("TestB", status_code=200)

    async def dummy(*args, **kwargs):
        ...

    app = StateRouterMiddleware(
        dummy, statemachine=StateMachine(TestStateA.goes_to(TestStateB))
    )
    await events.emit(StartupEvent())

    response = TestClient(app).get("/")
    assert response.text == "TestA"

    await app.statemachine.cycle()

    response = TestClient(app).get("/")
    assert response.text == "TestB"
