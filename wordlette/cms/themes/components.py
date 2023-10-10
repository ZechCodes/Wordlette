from abc import ABC, abstractmethod
from types import MethodType
from typing import Iterable, Callable

from markupsafe import Markup

from wordlette.core.html.renderables import Renderable


class Component(ABC, Renderable):
    @abstractmethod
    def compose(self) -> Iterable[Renderable]:
        ...

    def render(self) -> Markup:
        return Markup().join(renderable.render() for renderable in self.compose())


class ComponentDecorator(Component):
    def __init__(self, composer: Callable[[], Iterable[Renderable]]):
        self.composer = composer

    def compose(self) -> Iterable[Renderable]:
        return self.composer()

    def _create_composer_method(self, instance):
        composer = MethodType(self.composer, instance)

        def compose():
            return composer()

        return compose

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return self._create_composer_method(instance)


def component(composer: Callable[[], Iterable[Renderable]]) -> Component:
    return ComponentDecorator(composer)
