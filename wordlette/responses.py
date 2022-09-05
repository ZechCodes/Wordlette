import attrs
from starlette.responses import Response as StarletteResponse, HTMLResponse
from typing import Any, Type, TypeVar

from wordlette.bevy_utils import UnboundBevyContext

ResponseType = TypeVar("ResponseType", bound=StarletteResponse)


@attrs.define
class CookieInfo:
    key: str
    value: str
    max_age: int | None = None
    expires: int | None = None
    path: str = "/"
    domain: str | None = None
    secure: bool = False
    httponly: bool = False
    samesite: str = "lax"

    def asdict(self) -> dict[str, Any]:
        return attrs.asdict(self)


class Response:
    bevy = UnboundBevyContext()
    response_type: Type[ResponseType] = HTMLResponse

    def __init__(self, content: str = "", headers: dict[str, str] | None = None):
        self.cookies: dict[str, CookieInfo] = {}
        self.headers = headers is None and {} or headers
        self.content = ""
        self.status_code = 200

    async def create_response(self) -> ResponseType:
        bound_type: Type[ResponseType] = self.bevy.bind(self.response_type)
        response = await self._create_response_instance(bound_type)
        await self._setup_response(response)
        return response

    async def _create_response_instance(
        self, response_type: Type[ResponseType]
    ) -> ResponseType:
        return response_type(
            content=self.content, status_code=self.status_code, headers=self.headers
        )

    async def _set_response_cookies(self, response: ResponseType):
        for cookie in self.cookies.values():
            response.set_cookie(**cookie.asdict())

    async def _setup_response(self, response: ResponseType):
        await self._set_response_cookies(response)

    def delete_cookie(
        self,
        key: str,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str | None = "lax",
    ) -> None:
        self.set_cookie(
            key,
            max_age=0,
            expires=0,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )

    def set_cookie(
        self,
        key: str,
        value: str,
        max_age: int | None = None,
        expires: int | None = None,
        path: str = "/",
        domain: str | None = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: str = "lax",
    ):
        self.cookies[key] = CookieInfo(
            key, value, max_age, expires, path, domain, secure, httponly, samesite
        )

    def set_header(self, name: str, value: str):
        self.headers[name] = value
