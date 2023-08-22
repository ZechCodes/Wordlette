from typing import Type

from bevy import dependency
from starlette.types import Scope, Send, Receive

from wordlette.events import Observer
from wordlette.middlewares import Middleware
from wordlette.routers import Router
from wordlette.routes import Route
from wordlette.utils.apply import apply


class RouteManager:
    def __init__(self):
        super().__init__()
        self._router: Router | None = None

    @property
    def router(self) -> Router:
        if not self._router:
            self.create_router()

        return self._router

    @router.setter
    def router(self, router):
        if not isinstance(router, Router):
            raise TypeError(f"router must be an instance of {Router.__qualname__}")

        self._router = router

    def add_route(self, route: Type[Route]):
        self.router.add_route(route)

    def create_router(self, *routes: Type[Route]):
        self.router = Router()
        apply(self.add_route).to(routes)


class RouterMiddleware(Middleware, Observer):
    route_manager: RouteManager = dependency()

    async def run(self, scope: Scope, receive: Receive, send: Send):
        await self.route_manager.router(scope, receive, send)
