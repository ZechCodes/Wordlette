from wordlette.events import Event
from wordlette.core.requests import Request


class RequestEvent(Event):
    def __init__(self, request: Request):
        self._request = request

    @property
    def request(self) -> Request:
        return self._request

    @classmethod
    def factory(cls, request: Request) -> Event:
        match request:
            case Request.Get():
                event_type = GetRequestEvent

            case Request.Post():
                event_type = PostRequestEvent

            case Request.Put():
                event_type = PutRequestEvent

            case Request.Delete():
                event_type = DeleteRequestEvent

            case Request.Patch():
                event_type = PatchRequestEvent

            case Request.Head():
                event_type = HeadRequestEvent

            case _:
                event_type = cls

        return event_type(request)


class GetRequestEvent(RequestEvent):
    pass


class PostRequestEvent(RequestEvent):
    pass


class PutRequestEvent(RequestEvent):
    pass


class DeleteRequestEvent(RequestEvent):
    pass


class PatchRequestEvent(RequestEvent):
    pass


class HeadRequestEvent(RequestEvent):
    pass
