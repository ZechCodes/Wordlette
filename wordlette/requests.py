from typing import Type


class Request:
    Delete: "Type[Delete]"
    Get: "Type[Get]"
    Head: "Type[Head]"
    Patch: "Type[Patch]"
    Post: "Type[Post]"
    Put: "Type[Put]"

    def __init__(self, scope):
        self._scope = scope

    @property
    def name(self):
        return self._scope["method"].upper()

    @property
    def scope(self):
        return self._scope

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
