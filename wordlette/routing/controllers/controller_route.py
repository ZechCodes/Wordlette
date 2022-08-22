from __future__ import annotations
import wordlette.routing.controllers as controllers
from wordlette.routing.route import Route
from typing import Protocol
from wordlette.predicates import Predicate


class ControllerRoute(Route, Protocol):
    @classmethod
    def add_controller_schema(cls, schema: controllers.ControllerSchema):
        ...

    @classmethod
    def add_predicated_controller_schema(
        cls, predicate: Predicate, schema: controllers.ControllerSchema
    ):
        ...
