from abc import ABCMeta
from typing import get_origin, get_args, Annotated, TypeVar

from bevy.options import Null, Value, Option
from bevy.provider_state import ProviderState
from bevy.providers import AnnotatedProvider
from bevy.providers.provider import NotSupported

from wordlette.utils.annotated_aggregator import AnnotatedAggregator

T = TypeVar("T")


class AtAnnotationMCS(ABCMeta):
    def __rmatmul__(self, other: T) -> T:
        return AnnotatedAggregator[other, self()]


class AtAnnotation(metaclass=AtAnnotationMCS):
    __match_args__ = ("strategy",)

    def __rmatmul__(self, other):
        return AnnotatedAggregator[other, self]


class AtProvider(AnnotatedProvider):
    def create(self, key: T, cache: ProviderState) -> Option[T]:
        if not self.supports(key, cache):
            return NotSupported(f"{type(self)!r} does not support {key!r}")

        match get_args(key):
            case (type_, AtAnnotation(strategy)):
                return Value(strategy(type_, cache)())

            case Null(message):
                return Null(message)

    def supports(self, key, _) -> bool:
        if not get_origin(key) is Annotated:
            return False

        match get_args(key):
            case (_, AtAnnotation()):
                return True

            case _:
                return False
