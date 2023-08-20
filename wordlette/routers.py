from types import UnionType
from typing import Callable, get_args, Type, overload

from starlette.applications import Starlette
from starlette.types import Scope, Receive, Send

import wordlette.routes
from wordlette.expand_dict import expand_dict
from wordlette.requests import Request


class Router:
    def __init__(self):
        self.app = Starlette()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        return await self.app(scope, receive, send)

    @overload
    def add_route(
        self,
        route: "wordlette.routes.Route",
        include_in_schema: bool = True,
    ):
        ...

    @overload
    def add_route(
        self,
        path: str,
        route: Callable,
        methods: list[Type[Request]] | Type[Request] | UnionType = Request.Get,
        name: str = "",
        include_in_schema: bool = True,
    ):
        ...

    def add_route(self, path: "str | wordlette.routes.Route", **kwargs):
        match path:
            case str():
                self._add_new_route(
                    path,
                    *expand_dict(kwargs)(
                        route=...,
                        methods=Request.Get,
                        name="",
                        include_in_schema=True,
                    ),
                )

            case wordlette.routes.Route as route:
                self._add_route(route, *expand_dict(kwargs)(include_in_schema=True))

    def _add_route(self, route: "wordlette.routes.Route", include_in_schema: bool):
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
        self.app.add_route(
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
