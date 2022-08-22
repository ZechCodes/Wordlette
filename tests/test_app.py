from wordlette.app import App
from wordlette.state_machine import StateMachine, State
from wordlette.routing.page import Page, default, when
from bevy import Context, Inject, bevy_method
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.requests import Request
import httpx
import pytest


@pytest.mark.asyncio
async def test_app_using_query_predicate():
    class TestPage(Page):
        path = "/"

        index = default(HTMLResponse("Hello World"))

        @bevy_method
        async def is_test_2(self, request: Request = Inject):
            return request.query_params.get("test") == "2"

        test_2 = when(is_test_2).use(HTMLResponse("TEST 2"))

    async def build_page_handler(request):
        context = app.context.branch()
        context.add(request, use_as=type(request))
        page = TestPage()
        page.bevy = context
        return await page()

    class TestAppStateMachine(StateMachine):
        @State
        async def starting(self, app) -> Context:
            app = Starlette()
            app.add_route("/", build_page_handler)
            context = Context.factory()
            context.add(app, use_as=Starlette)
            return context

    app = App(TestAppStateMachine)
    async with httpx.AsyncClient(app=app) as client:
        resp = await client.get("http://localhost/")
        assert resp.content.decode() == "Hello World"

        resp = await client.get("http://localhost/?test=2")
        assert resp.content.decode() == "TEST 2"
