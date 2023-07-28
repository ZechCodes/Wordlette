from typing import Sequence, Protocol, runtime_checkable, Type

from bevy import get_repository
from starlette.routing import Router
from starlette.types import Scope, Send, Receive

from wordlette.app.app import StartupEvent
from wordlette.events import Observer
from wordlette.middlewares import Middleware
from wordlette.routes import Route
from wordlette.state_machines import StateMachine


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
        for route in routes:
            self.add_route(route)


class StateRouterMiddleware(Middleware, Observer):
    def __init__(self, *args, statemachine: StateMachine):
        super().__init__(*args)
        self.statemachine = statemachine
        self.route_manager = get_repository().get(RouteManager)
        self.run = self._startup_run

    def on_startup(self, _: StartupEvent):
        return self._startup()

    def _startup(self):
        self.run = self._run
        return self.statemachine.cycle()

    async def _startup_run(self, scope: Scope, receive: Receive, send: Send):
        await self._startup()
        await self.run(scope, receive, send)

    async def _run(self, scope: Scope, receive: Receive, send: Send):
        await self.route_manager.router(scope, receive, send)
        await self.next()
