from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def home(request):
    return PlainTextResponse("Test")


app = Starlette(
    routes=[
        Route("/", home),
    ]
)
