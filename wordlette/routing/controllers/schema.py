from __future__ import annotations
from typing import Any, Awaitable, Callable, Type
from wordlette.routing.controllers.controller_route import ControllerRoute
from wordlette.predicates import Predicate, AndPredicate
from starlette.requests import Request
from starlette.responses import Response


ControllerFunction = Callable[[], Awaitable[Any]]
OnSubmitFunction = Callable[[Request], Awaitable[Any | None]]


def ensure_controller_function(controller) -> ControllerFunction:
    """Takes an object and ensures it is callable and not a response type. If it is not callable or is a response type,
    it will be wrapped in an async function that will return the object.

    A controller should return an awaitable. This is not something that can be trivially guaranteed since a callable
    could return an awaitable without annotations to indicate as much. So, this just ensures that the controller is a
    callable and will fail later if it doesn't return an awaitable."""
    if callable(controller) and not isinstance(controller, Response):
        return controller

    async def controller_wrapper(*_, **__):
        return controller

    return controller_wrapper


class ControllerSchema:
    def __init__(
        self,
        controller_function: ControllerFunction,
        predicate: Predicate | None = None,
        parent_controller: ControllerSchema | None = None,
        on_submit: OnSubmitFunction | None = None,
    ):
        self._controller = ensure_controller_function(controller_function)
        self._predicate = predicate
        self._parent_controller = parent_controller
        self._on_submit: OnSubmitFunction | None = on_submit

    @property
    def controller(self) -> ControllerFunction:
        return self._controller

    @property
    def process_form(self) -> OnSubmitFunction:
        if self._on_submit:
            return self._on_submit

        if self._parent_controller:
            return self._parent_controller.process_form

        async def null_form_processor(*_, **__):
            return

        return null_form_processor

    def on_submit(self, submit_function: OnSubmitFunction):
        self._on_submit = submit_function

    def when(
        self, predicate: Predicate | Callable[[], Awaitable[bool]]
    ) -> PredicatedControllerBuilder:
        if not isinstance(predicate, Predicate):
            predicate = AndPredicate(predicate)

        return PredicatedControllerBuilder(predicate, self)

    def __set_name__(self, owner: Type[ControllerRoute], _):
        if self._predicate:
            owner.add_predicated_controller_schema(self._predicate, self)
        else:
            owner.add_controller_schema(self)


class PredicatedControllerBuilder:
    def __init__(self, predicate: Predicate, parent_controller: ControllerSchema):
        self.predicate = predicate
        self.parent = parent_controller

    def use(self, controller: ControllerFunction) -> ControllerSchema:
        return ControllerSchema(controller, self.predicate, self.parent)

    def fail_using(self, controller: ControllerFunction) -> ControllerSchema:
        return ControllerSchema(controller, self.predicate)
