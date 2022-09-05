from starlette.responses import Response, HTMLResponse

from wordlette.pages import Page


class Blog(Page):
    path = "/blog/{post_id:int}"

    async def response(self, post_id: int) -> str:
        return f"Hello World - {post_id!r}".encode()

    async def on_error_show_runtime_error_message(
        self, error: RuntimeError
    ) -> Response:
        return HTMLResponse("There was a runtime error")
