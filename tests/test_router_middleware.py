import pytest
from bevy import get_repository
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.middlewares.router_middleware import RouteManager, RouterMiddleware
from wordlette.requests import Request
from wordlette.routes import Route


@pytest.mark.asyncio
async def test_router():
    repo = get_repository()
    repo.set(RouteManager, router := RouteManager())

    async def dummy(*args, **kwargs):
        ...

    app = RouterMiddleware(dummy)
    router.router.add_route("/", route=PlainTextResponse("Test", status_code=200))
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Test"


@pytest.mark.asyncio
async def test_router_with_route():
    repo = get_repository()
    repo.set(RouteManager, router := RouteManager())

    async def dummy(*args, **kwargs):
        ...

    class TestRoute(Route):
        path = "/"

        async def index_get(self, request: Request.Get):
            return PlainTextResponse("Test", status_code=200)

    app = RouterMiddleware(dummy)
    router.create_router(TestRoute)
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert response.text == "Test"
