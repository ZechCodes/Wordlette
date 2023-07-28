from bevy import get_repository
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Scope, Send, Receive

from wordlette.app.app import StartupEvent
from wordlette.events import Observer
from wordlette.middlewares import Middleware
from wordlette.state_machines import StateMachine


class RouteManager:
    def __init__(self):
        super().__init__()
        self._router = PlainTextResponse("No router is configured", status_code=500)

    @property
    def router(self) -> ASGIApp:
        return self._router

    @router.setter
    def router(self, router):
        self._router = router


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
