from typing import Type, Callable

from bevy import dependency, get_repository
from starlette.responses import Response
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
        self._error_pages: dict[int, Callable[[int, Scope], Response]] = {}

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
        get_repository().set(Router, self._router)

    def add_error_page(
        self, status_code: int, get_page: Callable[[int, Scope], Response]
    ):
        self._error_pages[status_code] = get_page
        if self._router:
            self._router.add_error_page(status_code, get_page)

    def add_route(self, route: Type[Route]):
        self.router.add_route(route)

    def create_router(self, *routes: Type[Route]):
        self.router = Router()
        apply(self.add_route).to(routes)
        apply(self.add_error_page).to(
            self._error_pages.keys(), self._error_pages.values()
        )

    def url_for(self, route: Type[Route], **path_params) -> str:
        return self.router.url_for(route, **path_params)


class RouterMiddleware(Middleware, Observer):
    route_manager: RouteManager = dependency()

    async def run(self, scope: Scope, receive: Receive, send: Send):
        await self.route_manager.router(scope, receive, send)
