from bevy import Bevy
from typing import Type

from wordlette.routing.controllers import (
    Controller,
    ControllerSchema,
    ControllerSchemaCollection,
)
from wordlette.predicates import Predicate


def controller(controller_function):
    return ControllerSchema(controller_function)


class Page(Bevy):
    __slots__ = ("_controller", "_predicated_controllers")

    path: str
    controller_schema: ControllerSchema | None = None
    predicated_controller_schemas: dict[
        Predicate, ControllerSchema
    ] = ControllerSchemaCollection()

    @classmethod
    def add_controller_schema(cls, schema: ControllerSchema):
        cls.controller_schema = schema

    @classmethod
    def add_predicated_controller_schema(
        cls, predicate: Predicate, schema: ControllerSchema
    ):
        cls.predicated_controller_schemas[predicate] = schema

    async def __call__(self):
        _BoundController = self.bevy.bind(Controller)
        self._controller: Type[Controller] = _BoundController(self.controller_schema)
        self._predicated_controllers: dict[Predicate, Controller] = {
            predicate: _BoundController(controller_schema)
            for predicate, controller_schema in self.predicated_controller_schemas.items()
        }
        return await self.get_response()

    async def get_response(self):
        for p, c in self._predicated_controllers.items():
            if await p(self):
                break
        else:
            c = self._controller

        return await c.respond(self)
