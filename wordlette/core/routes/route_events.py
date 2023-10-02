from starlette.responses import Response

from wordlette.core.requests import Request
from wordlette.events import Event
from wordlette.models import Model, FieldSchema


class ResponseEvent(Event, Model):
    response: Response @ FieldSchema


class RequestEvent(Event, Model):
    request: Request @ FieldSchema

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
