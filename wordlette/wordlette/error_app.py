from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class ErrorMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, message: str, title: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.title = title

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path != "/":
            return RedirectResponse("/")

        return HTMLResponse(
            f"<title>Wordlette - 400 {self.title}</title><h1>Wordlette - 400 {self.title}</h1><p>{self.message}</p>",
            400,
        )


def create_error_application(message: str, title: str):
    app = Starlette()
    app.add_middleware(ErrorMiddleware, message=message, title=title)
    return app
