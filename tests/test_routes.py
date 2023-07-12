from pytest import raises
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.requests import Request
from wordlette.routes import Route, MissingRoutePath


def test_route_exception_handler_detection():
    class TestRoute(Route):
        path = "/"

        async def handle_exception(self, error: Exception):
            pass

        async def handle_value_error(self, error: ValueError):
            pass

    assert TestRoute.error_handlers == {
        Exception: TestRoute.handle_exception,
        ValueError: TestRoute.handle_value_error,
    }


def test_route_request_type_handler_detection():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, request: Request.Get):
            pass

        async def handle_post_request(self, request: Request.Post):
            pass

    assert TestRoute.request_handlers == {
        Request.Get: TestRoute.handle_get_request,
        Request.Post: TestRoute.handle_post_request,
    }


def test_route_union_type_handler_detection():
    class TestRoute(Route):
        path = "/"

        async def handle_request(self, request: Request.Get | Request.Post):
            pass

    assert TestRoute.request_handlers == {
        Request.Get: TestRoute.handle_request,
        Request.Post: TestRoute.handle_request,
    }


def test_route_handling():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, _: Request.Get):
            return PlainTextResponse("testing")

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "testing"


def test_route_handling_with_multiple_methods():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, _: Request.Get):
            return PlainTextResponse("testing get")

        async def handle_post_request(self, _: Request.Post):
            return PlainTextResponse("testing post")

    client = TestClient(TestRoute())
    assert client.get("/").text == "testing get"
    assert client.post("/").text == "testing post"


def test_route_handling_with_union_methods():
    class TestRoute(Route):
        path = "/"

        async def handle_request(self, request: Request.Get | Request.Post):
            return PlainTextResponse(f"testing {request.method}")

    client = TestClient(TestRoute())
    assert client.get("/").text == "testing GET"
    assert client.post("/").text == "testing POST"


def test_route_exception_handling():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, request: Request.Get):
            raise ValueError("testing value error")

        async def handle_value_errors(self, exception: ValueError):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 500
    assert response.text == "testing value error"


def test_route_exception_handling_super_types():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, request: Request.Get):
            raise ValueError("testing value error")

        async def handle_value_errors(self, exception: Exception):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 500
    assert response.text == "testing value error"


def test_route_exception_handling_sub_types():
    class TestRoute(Route):
        path = "/"

        async def handle_get_request(self, request: Request.Get):
            raise Exception("testing value error")

        async def handle_value_errors(self, exception: ValueError):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    with raises(Exception):
        response = client.get("/")


def test_missing_route_path():
    with raises(MissingRoutePath):

        class TestRoute(Route):
            ...
