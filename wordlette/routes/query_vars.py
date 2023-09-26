from typing import Any

from bevy import get_repository
from bevy.options import Value as _Value, Null as _Null

from wordlette.requests import Request
from wordlette.utils.at_annotateds import AtAnnotation
from wordlette.utils.options import Null


class QueryArg(AtAnnotation):
    def __init__(self, key: str, default: Any = Null()):
        self.key = key
        self.default = default

    def _get_request(self) -> Request | None:
        repo = get_repository()
        match repo.find(Request):
            case _Null():
                return None

            case _Value(request):
                return request

    def strategy(self, *_):
        request = self._get_request()
        if request is None:
            return lambda: self.default

        match self.default:
            case Null():
                raise Exception("No request found")

            case _:
                return lambda: request.query_params.get(self.key, self.default)
