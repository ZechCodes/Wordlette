from typing import Type, Any, Callable, cast

import wordlette.routes as routes
from wordlette.forms import Form
from wordlette.requests import Request


def create_metadata_type(
    *bases: "Type[RouteMetadata]" | Type, **properties: Any
) -> "Type[RouteMetadata]":
    return cast(
        Type[RouteMetadata],
        type(
            "__metadata__",
            bases,
            properties,
        ),
    )


def get_super_route(cls):
    for base in cls.__bases__:
        if base is routes.Route or issubclass(base, routes.Route):
            return base


class RouteMetadata:
    abstract: bool
    registry: "set[Type[routes.Route]]"
    error_handlers: dict[Type[Exception], Callable[[Exception], Any]]
    request_handlers: dict[Type[Request], Callable[[Request], Any]]
    form_handlers: dict[Type[Form], Callable[[Form], Any]]


class RouteMetadataSetup:
    class __metadata__(RouteMetadata):
        abstract = True
        registry = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if RouteMetadataSetup in cls.__bases__:
            return

        cls._setup_metadata()

    @classmethod
    def _create_new_metadata_object(cls):
        super_route = get_super_route(cls)
        cls.__metadata__ = create_metadata_type(
            super_route.__metadata__,
            abstract=False,
            request_handlers={},
            error_handlers={},
            form_handlers={},
        )

    @classmethod
    def _setup_metadata(cls):
        if cls.__metadata__ is get_super_route(cls).__metadata__:
            cls._create_new_metadata_object()

        elif not issubclass(cls.__metadata__, RouteMetadata):
            cls._transform_metadata_to_metadata_type()

    @classmethod
    def _transform_metadata_to_metadata_type(cls):
        super_route = get_super_route(cls)

        if not hasattr(cls.__metadata__, "request_handlers"):
            cls.__metadata__.request_handlers = {}

        if not hasattr(cls.__metadata__, "error_handlers"):
            cls.__metadata__.error_handlers = {}

        if not hasattr(cls.__metadata__, "form_handlers"):
            cls.__metadata__.form_handlers = {}

        cls.__metadata__ = create_metadata_type(
            cls.__metadata__, super_route.__metadata__
        )
