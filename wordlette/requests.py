from typing import Type


class Request:
    Delete: "Type[DeleteRequest]"
    Get: "Type[GetRequest]"
    Head: "Type[HeadRequest]"
    Patch: "Type[PatchRequest]"
    Post: "Type[PostRequest]"
    Put: "Type[PutRequest]"

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


class DeleteRequest(Request):
    ...


class GetRequest(Request):
    ...


class HeadRequest(Request):
    ...


class PatchRequest(Request):
    ...


class PostRequest(Request):
    ...


class PutRequest(Request):
    ...


Delete = Request.Delete = DeleteRequest
Get = Request.Get = GetRequest
Head = Request.Head = HeadRequest
Patch = Request.Patch = PatchRequest
Post = Request.Post = PostRequest
Put = Request.Put = PutRequest
