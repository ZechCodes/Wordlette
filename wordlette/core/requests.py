from typing import Type

from starlette.requests import Request as StarletteRequest, empty_receive, empty_send


class Request(StarletteRequest):
    Delete: "Type[Delete]"
    Get: "Type[Get]"
    Head: "Type[Head]"
    Patch: "Type[Patch]"
    Post: "Type[Post]"
    Put: "Type[Put]"

    name: str

    def __init_subclass__(cls, **kwargs):
        cls.name = cls.__name__.upper()

    @classmethod
    def factory(cls, scope, receive=empty_receive, send=empty_send) -> "Request":
        match scope["method"].upper():
            case "DELETE":
                request_type = cls.Delete

            case "GET":
                request_type = cls.Get

            case "HEAD":
                request_type = cls.Head

            case "PATCH":
                request_type = cls.Patch

            case "POST":
                request_type = cls.Post

            case "PUT":
                request_type = cls.Put

            case _:
                request_type = Request

        return request_type(scope, receive, send)


class Delete(Request):
    ...


class Get(Request):
    ...


class Head(Request):
    ...


class Patch(Request):
    ...


class Post(Request):
    ...


class Put(Request):
    ...


Request.Delete = Delete
Request.Get = Get
Request.Head = Head
Request.Patch = Patch
Request.Post = Post
Request.Put = Put
