from typing import Type

from starlette.requests import Request as StarletteRequest


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
    def factory(cls, scope) -> "Request":
        match scope["method"].upper():
            case "DELETE":
                return cls.Delete(scope)

            case "GET":
                return cls.Get(scope)

            case "HEAD":
                return cls.Head(scope)

            case "PATCH":
                return cls.Patch(scope)

            case "POST":
                return cls.Post(scope)

            case "PUT":
                return cls.Put(scope)

            case _:
                return Request(scope)


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
