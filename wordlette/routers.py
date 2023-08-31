import logging
from types import UnionType
from typing import Callable, get_args, Type, overload

from bevy import get_repository, inject, dependency
from starlette.exceptions import HTTPException
from starlette.responses import Response, HTMLResponse
from starlette.routing import Router as _StarletteRouter
from starlette.types import Scope, Receive, Send

import wordlette.routes
from wordlette.core.app import AppSetting
from wordlette.requests import Request
from wordlette.utils.expand_dicts import from_dict

logger = logging.getLogger("Router")


class StarletteRouter(_StarletteRouter):
    async def not_found(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            return await super().not_found(scope, receive, send)

        raise HTTPException(status_code=404)


class Router:
    def __init__(self):
        self.router = StarletteRouter()
        self.error_pages: dict[int, Callable[[int, Scope], Response]] = {}

    @inject
    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        debug: bool @ AppSetting("debug", False) = dependency(),
    ):
        try:
            return await self.router(scope, receive, send)

        except Exception as exc:
            if debug:
                scope["exception"] = exc

            page = self._get_error_page(getattr(exc, "status_code", 500), scope)
            if not isinstance(exc, HTTPException):
                logger.exception(
                    "The router encountered an error while running the route handler."
                )

            await page(scope, receive, send)

    def add_error_page(
        self, status_code: int, get_page: Callable[[int, Scope], Response]
    ):
        self.error_pages[status_code] = get_page

    @overload
    def add_route(
        self,
        route: "type[wordlette.routes.Route]",
        include_in_schema: bool = True,
    ):
        ...

    @overload
    def add_route(
        self,
        path: str,
        *,
        route: Callable,
        methods: list[Type[Request]] | Type[Request] | UnionType = Request.Get,
        name: str = "",
        include_in_schema: bool = True,
    ):
        ...

    def add_route(self, path_or_route: "str | Type[wordlette.routes.Route]", **kwargs):
        match path_or_route:
            case str():
                self._add_new_route(
                    path_or_route,
                    *from_dict(kwargs).get_values(
                        route=...,
                        methods=Request.Get,
                        name="",
                        include_in_schema=True,
                    ),
                )

            case wordlette.routes.Route.matches_type() as route_type:
                self._add_route_type(
                    route_type, *from_dict(kwargs).get_values(include_in_schema=True)
                )

            case _:
                raise TypeError(f"{path_or_route!r} is not a valid route type")

    def url_for(self, route: "type[wordlette.routes.Route]", **path_params) -> str:
        return self.router.url_path_for(route.name, **path_params)

    def _404_error_page(self, status_code: int, scope: Scope) -> Response:
        return HTMLResponse(
            f"<h1>{status_code}: Page Not Found</h1><p>Wordlette couldn't find any resources at <code>{scope['path']}</code>.<p>",
            status_code,
        )

    def _generate_error_page(self, status_code: int, scope: Scope) -> Response:
        return HTMLResponse(
            f"<h1>{status_code}: Error Encountered</h1><p>Wordlette encountered an error and couldn't recover.<p><pre>{scope['exception']!r}</pre>",
            status_code,
        )

    def _generic_error_page(self, status_code: int, scope: Scope) -> Response:
        return HTMLResponse(
            f"<h1>{status_code}: Error Encountered</h1><p>Wordlette encountered an error and couldn't recover.<p>",
            status_code,
        )

    def _add_route_type(
        self, route_type: "Type[wordlette.routes.Route]", include_in_schema: bool = True
    ):
        route = get_repository().get(route_type)
        self._add_new_route(
            route.path, route, route.methods.names, route.name, include_in_schema
        )

    def _add_new_route(
        self,
        path: str,
        route: Callable,
        methods: list[Type[Request]] | Type[Request] | UnionType,
        name: str,
        include_in_schema: bool,
    ):
        self.router.add_route(
            path,
            route,
            self._build_methods_list(methods),
            name or None,
            include_in_schema,
        )

    def _build_methods_list(
        self, methods: list[Type[Request] | str] | Type[Request] | str | UnionType
    ) -> list[str]:
        match methods:
            case [*values] if all(isinstance(value, str) for value in values):
                return [method.upper() for method in methods]

            case [*values] if all(issubclass(value, Request) for value in values):
                return [method.__name__.upper() for method in methods]

            case str() as method:
                return [method.upper()]

            case type() if issubclass(methods, Request):
                return [methods.__name__.upper()]

            case UnionType() as values:
                return self._build_methods_list(list(get_args(values)))

            case _:
                raise TypeError("Invalid type for methods")

    def _get_error_page(self, status_code: int, scope: Scope) -> Response:
        page = self._generic_error_page
        if status_code in self.error_pages:
            page = self.error_pages[status_code]

        elif 0 in self.error_pages:
            page = self.error_pages[0]

        elif status_code == 404:
            page = self._404_error_page

        elif status_code == 500 and "exception" in scope:
            page = self._generate_error_page

        return page(status_code, scope)
