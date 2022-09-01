import pytest
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette.responses import HTMLResponse

from wordlette.app import App
from wordlette.forms import Form, Field
from wordlette.pages import Page
from wordlette.state_machine import StateMachine, State


def create_state_machine(page):
    class TestStateMachine(StateMachine):
        @State
        async def starting(self, app):
            context = self.bevy.branch()
            site = Starlette()
            page.register(site)
            context.add(site, use_as=Starlette)
            return context

    return TestStateMachine


def create_app(page):
    return App(create_state_machine(page))


@pytest.mark.asyncio
async def test_page_get_url_parameter():
    response_content = "Test Response"
    request_word = "Parameter"

    class TestPage(Page):
        path = "/{word}"

        async def response(self, word):
            return HTMLResponse(f"{response_content} - {word}")

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.get(f"http://localhost:8000/{request_word}")

    assert response.status_code == 200
    assert response.content.decode() == f"{response_content} - {request_word}"


@pytest.mark.asyncio
async def test_page_post():
    submit_value = "test field"

    class TestForm(Form):
        test_field: str

    class TestPage(Page):
        path = "/"

        def __init__(self):
            self.message = "NO SUBMIT"

        async def response(self, form: TestForm):
            return HTMLResponse(f"{form.test_field} {self.message}")

        async def on_form_submit(self, form: TestForm):
            self.message = form.test_field
            return form

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.post(
            f"http://localhost:8000/", data={"test_field": submit_value}
        )

    # assert response.status_code == 200
    assert response.content.decode() == f"{submit_value} {submit_value}"


@pytest.mark.asyncio
async def test_page_post_optional_fields():
    submit_value = "test field"

    class TestForm(Form):
        test_field: str
        testing_optionals: int = Field(optional=True)

    class TestPage(Page):
        path = "/"

        def __init__(self):
            self.message = "NO SUBMIT"

        async def response(self, form: TestForm):
            return HTMLResponse(f"{form.test_field} {self.message}")

        async def on_form_submit(self, form: TestForm):
            self.message = form.test_field
            return form

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.post(
            f"http://localhost:8000/", data={"test_field": submit_value}
        )

    assert response.content.decode() == f"{submit_value} {submit_value}"


@pytest.mark.asyncio
async def test_page_error_handlers():
    response_content = "Test Exception Response"
    status_code = 500

    class TestPage(Page):
        path = "/"

        async def response(self):
            raise RuntimeError(response_content)

        async def on_test_error_response(self, error: RuntimeError):
            return HTMLResponse(error.args[0], status_code=status_code)

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.get("http://localhost:8000/")

    assert response.status_code == status_code
    assert response.content.decode() == response_content


@pytest.mark.asyncio
async def test_page_union_error_handlers():
    response_content = "Test Exception Response"
    status_code = 500

    class TestPage(Page):
        path = "/"

        async def response(self):
            raise RuntimeError(response_content)

        async def on_test_error_response(self, error: RuntimeError | ZeroDivisionError):
            return HTMLResponse(error.args[0], status_code=status_code)

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.get("http://localhost:8000/")

    assert response.status_code == status_code
    assert response.content.decode() == response_content


@pytest.mark.asyncio
async def test_page_error_in_error_handler():
    response_content_a = "Test Exception Response A"
    response_content_b = "Test Exception Response B"
    status_code = 500

    class TestPage(Page):
        path = "/"

        async def response(self):
            raise RuntimeError(response_content_a)

        async def on_test_error_response(self, error: RuntimeError):
            raise RuntimeError(response_content_b)

    app = create_app(TestPage)
    async with AsyncClient(app=app) as client:
        response = await client.get("http://localhost:8000/")

    content = response.content.decode()
    assert response.status_code == status_code
    assert response_content_a in content
    assert response_content_b in content
