from __future__ import annotations
from bevy import Bevy, bevy_method, Inject
import wordlette.routing.controllers as controllers
from starlette.requests import Request
from typing import Any, Awaitable


class Controller(Bevy):
    def __init__(self, schema: controllers.ControllerSchema):
        self._schema = schema
        self._process_form_function = None

    @bevy_method
    async def process_form(self, request: Request = Inject):
        form = await self._process_form(self, request)
        if form:
            self.bevy.add(form, use_as=type(form))

    @bevy_method
    async def respond(self, page, request: Request = Inject):
        if request.method == "POST":
            await self.process_form()

        return await self._schema.controller(page)

    def _process_form(self, *args, **kwargs) -> Awaitable[Any | None]:
        if not self._process_form_function:
            self._process_form_function = self.bevy.bind(self._schema.process_form)

        return self._process_form_function(*args, **kwargs)
