from starlette.testclient import TestClient

from wordlette.app import WordletteApp
from wordlette.middlewares import Middleware


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
