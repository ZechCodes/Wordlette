from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.requests import Request
from wordlette.routers import Router


def test_build_request_types_request():
    assert Router()._build_methods_list(Request.Get) == ["GET"]


def test_build_request_types_union():
    assert Router()._build_methods_list(Request.Get | Request.Post) == ["GET", "POST"]


def test_build_request_types_list():
    assert Router()._build_methods_list([Request.Get, Request.Post]) == ["GET", "POST"]


def test_build_request_types_string():
    assert Router()._build_methods_list("GET") == ["GET"]


def test_build_request_types_strings():
    assert Router()._build_methods_list(["GET", "POST"]) == ["GET", "POST"]


def test_router_routing():
    router = Router()
    router.add_route("/", PlainTextResponse("Index"), Request.Get)
    router.add_route("/test", PlainTextResponse("Test"), Request.Get)

    client = TestClient(router)
    assert client.get("/").text == "Index"
    assert client.get("/test").text == "Test"


def test_router_routing_multiple_methods():
    router = Router()
    router.add_route("/", PlainTextResponse("Index"), Request.Get | Request.Post)

    client = TestClient(router)
    assert client.get("/").text == "Index"
    assert client.post("/").text == "Index"


def test_router_routing_incorrect_method():
    router = Router()
    router.add_route("/", PlainTextResponse("Index"), Request.Get)

    client = TestClient(router)
    assert client.post("/").status_code == 405