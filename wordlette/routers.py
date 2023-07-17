from types import UnionType
from typing import Callable, get_args, Type

from starlette.applications import Starlette

from wordlette.requests import Request


class Router:
    def __init__(self):
        self.app = Starlette()

    async def __call__(self, *args, **kwargs):
        return await self.app(*args, **kwargs)

    def add_route(
        self,
        path: str,
        route: Callable,
        methods: list[Type[Request]] | Type[Request] | UnionType = Request.Get,
        name: str = "",
        include_in_schema: bool = True,
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
