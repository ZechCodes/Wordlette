from typing import Type


class ExceptionHandlerContext:
    """When an exception occurs in a route, the exception handler context finds a matching handler on the route. If no
    handler is found the exception will be allowed to propagate. Calling the context object after it has found a handler
    runs the handler and its response, sending the response to the client."""

    def __init__(self, route):
        self.route = route
        self.exception = None
        self.handler = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if handler := self._find_error_handler(exc_type):
            self.handler = handler
            self.exception = exc_val
            return True

    def __bool__(self):
        return self.exception is not None

    async def __call__(self, scope, receive, send):
        response = await self.handler(self.route, self.exception)
        await response(scope, receive, send)

    def _find_error_handler(self, exception_type: Type[Exception]):
        for error_type, handler in self.route.__metadata__.error_handlers.items():
            if exception_type is error_type or (
                isinstance(exception_type, type)
                and issubclass(exception_type, error_type)
            ):
                return handler
