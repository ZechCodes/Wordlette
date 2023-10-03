from typing import Type, cast

from wordlette.core.forms import Form
from wordlette.core.routes import Route
from wordlette.users.auth_security_levels import AuthSecurityLevel


class BaseAuthProvider:
    __auth_provider_registry__: "set[Type[BaseAuthProvider]]" = set()

    nice_name: str
    route: Type[Route]
    security_level: AuthSecurityLevel

    def __init_subclass__(
        cls,
        name: str | None = None,
        route_type: Type[Route] | None = None,
        security_level: AuthSecurityLevel | None = None,
        **kwargs,
    ):
        cls.nice_name = cls._determine_nice_name(name)
        cls.route = cls._determine_route_type(route_type)
        cls.security_level = cls._determine_security_level(security_level)

        cls._register_auth_provider()

        super().__init_subclass__(**kwargs)

    @classmethod
    def _determine_nice_name(cls, name: str | None) -> str:
        if name is not None:
            return name

        return getattr(cls, "nice_name", cls.__name__)

    @classmethod
    def _determine_route_type(cls, route_type: type[Route] | None) -> Type[Route]:
        _route = getattr(cls, "route", None)
        if route_type is not None:
            _route = route_type

        elif _route is None:
            name = f"{cls.__name__}_Route"
            metadata_type = type(f"{name}Metadata", (), {"registry": set()})
            _route = cast(
                Type[Route], type(name, (Route,), {"__metadata__": metadata_type})
            )

        return _route

    @classmethod
    def _determine_security_level(
        cls, security_level: AuthSecurityLevel | None
    ) -> AuthSecurityLevel:
        if security_level is not None:
            return security_level

        return getattr(cls, "security_level", AuthSecurityLevel.UNSAFE)

    @classmethod
    def register_auth_provider(cls):
        cls.__auth_provider_registry__.add(cls)

    @classmethod
    def unregister_auth_provider(cls):
        cls.__auth_provider_registry__.discard(cls)
