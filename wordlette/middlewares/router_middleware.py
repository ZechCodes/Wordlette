from typing import Sequence, Protocol, runtime_checkable, Type

from bevy import dependency
from starlette.routing import Router
from starlette.types import Scope, Send, Receive

from wordlette.apply import apply
from wordlette.events import Observer
from wordlette.middlewares import Middleware
from wordlette.routes import Route


@runtime_checkable
class RouterProtocol(Protocol):
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        ...

    def add_route(
        self,
        path: str,
        route: Route,
        methods: Sequence[str],
        name: str,
        *args,
        **kwargs,
    ):
        ...


class RouteManager:
    def __init__(self):
        super().__init__()
        self._router: RouterProtocol | None = None

    @property
    def router(self) -> RouterProtocol:
        if not self._router:
            self.create_router()

        return self._router

    @router.setter
    def router(self, router):
        if not isinstance(router, RouterProtocol):
            raise TypeError(f"router must adhere to the {RouterProtocol.__name__}")

        self._router = router

    def add_route(self, route: Type[Route]):
        self.router.add_route(
            route.path,
            route(),
            route.methods,
            route.name,
        )

    def create_router(self, *routes: Type[Route]):
        self.router = Router()
        apply(routes, self.add_route)


class RouterMiddleware(Middleware, Observer):
    route_manager: RouteManager = dependency()

    async def run(self, scope: Scope, receive: Receive, send: Send):
        await self.route_manager.router(scope, receive, send)
