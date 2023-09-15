from pytest import raises
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from wordlette.core.exceptions import MissingRoutePath, NoRouteHandlersFound
from wordlette.forms import Form
from wordlette.requests import Request
from wordlette.routes import Route
from wordlette.routes.exceptions import NoCompatibleFormError


class DefaultPathRoute(Route):
    path = "/"

    async def get(self, _: Request.Get):
        ...


def test_route_exception_handler_detection():
    class TestRoute(DefaultPathRoute):
        async def get(self, _: Request.Get):
            ...

        async def handle_exception(self, error: Exception):
            pass

        async def handle_value_error(self, error: ValueError):
            pass

    assert TestRoute.__metadata__.error_handlers == {
        Exception: TestRoute.handle_exception,
        ValueError: TestRoute.handle_value_error,
    }


def test_route_request_type_handler_detection():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, request: Request.Get):
            pass

        async def handle_post_request(self, request: Request.Post):
            pass

    assert TestRoute.__metadata__.request_handlers == {
        Request.Get: TestRoute.handle_get_request,
        Request.Post: TestRoute.handle_post_request,
    }


def test_route_union_type_handler_detection():
    class TestRoute(DefaultPathRoute):
        async def handle_request(self, request: Request.Get | Request.Post):
            pass

    assert TestRoute.__metadata__.request_handlers == {
        Request.Get: TestRoute.handle_request,
        Request.Post: TestRoute.handle_request,
    }


def test_route_handling():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, _: Request.Get):
            return PlainTextResponse("testing")

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "testing"


def test_route_handling_with_multiple_methods():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, _: Request.Get):
            return PlainTextResponse("testing get")

        async def handle_post_request(self, _: Request.Post):
            return PlainTextResponse("testing post")

    client = TestClient(TestRoute())
    assert client.get("/").text == "testing get"
    assert client.post("/").text == "testing post"


def test_route_handling_with_union_methods():
    class TestRoute(DefaultPathRoute):
        async def handle_request(self, request: Request.Get | Request.Post):
            return PlainTextResponse(f"testing {request.name}")

    client = TestClient(TestRoute())
    assert client.get("/").text == "testing GET"
    assert client.post("/").text == "testing POST"


def test_route_exception_handling():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, request: Request.Get):
            raise ValueError("testing value error")

        async def handle_value_errors(self, exception: ValueError):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 500
    assert response.text == "testing value error"


def test_route_exception_handling_super_types():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, request: Request.Get):
            raise ValueError("testing value error")

        async def handle_value_errors(self, exception: Exception):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    response = client.get("/")
    assert response.status_code == 500
    assert response.text == "testing value error"


def test_route_exception_handling_sub_types():
    class TestRoute(DefaultPathRoute):
        async def handle_get_request(self, request: Request.Get):
            raise Exception("testing value error")

        async def handle_value_errors(self, exception: ValueError):
            return PlainTextResponse(str(exception), 500)

    client = TestClient(TestRoute())
    with raises(Exception):
        _ = client.get("/")


def test_missing_route_path():
    with raises(MissingRoutePath):

        class TestRoute(Route):
            ...


def test_no_route_handlers():
    with raises(NoRouteHandlersFound):

        class TestRoute(Route):
            path = "/"


def test_route_registry():
    route_registry = set()

    class TestRouteAbstract(Route):
        class __metadata__:
            abstract = True
            registry = route_registry

    class TestRoute(TestRouteAbstract):
        path = "/"

        async def get(self, _: Request.Get):
            ...

    assert TestRoute in route_registry


def test_post_form_route():
    class TestForm(Form):
        string: str
        number: int

    class TestRoute(DefaultPathRoute):
        async def handle_form(self, form: TestForm):
            return PlainTextResponse(f"string: {form.string} number: {form.number}")

    client = TestClient(TestRoute())
    response = client.post("/", data={"string": "testing", "number": "123"})
    assert response.status_code == 200
    assert response.text == "string: testing number: 123"


def test_incompatible_form_type():
    class TestForm(Form):
        field: str

    class TestRoute(DefaultPathRoute):
        async def handle_form(self, form: TestForm):
            return

    client = TestClient(TestRoute())

    with raises(NoCompatibleFormError):
        response = client.post("/", data={"test": "bad data"})


def test_extra_form_fields():
    class TestForm(Form):
        field: str

    class TestRoute(DefaultPathRoute):
        async def handle_form(self, form: TestForm):
            return PlainTextResponse(form.field)

    client = TestClient(TestRoute())
    response = client.post("/", data={"field": "value", "extra": "extra value"})
    assert response.status_code == 200
    assert response.text == "value"


def test_multiple_forms():
    class TestFormA(Form):
        field_a: str

    class TestFormB(Form):
        field_a: str
        field_b: str

    class TestRoute(DefaultPathRoute):
        async def handle_form_a(self, form: TestFormA):
            return PlainTextResponse("A")

        async def handle_form_b(self, form: TestFormB):
            return PlainTextResponse("B")

    client = TestClient(TestRoute())
    response = client.post("/", data={"field_a": "a"})
    assert response.status_code == 200
    assert response.text == "A"

    response = client.post("/", data={"field_a": "a", "field_b": "b"})
    assert response.status_code == 200
    assert response.text == "B"
