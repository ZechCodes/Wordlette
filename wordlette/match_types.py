from typing import Type, TypeVar, cast

T = TypeVar("T")


class IsSubclassMCS(type):
    match_type: Type

    def __instancecheck__(self, instance):
        return isinstance(instance, type) and issubclass(instance, self.match_type)


def match_type(cls) -> IsSubclassMCS:
    return cast(
        Type[T], IsSubclassMCS(f"IsSubclass_{cls.__name__}", (), {"match_type": cls})
    )


class TypeMatchable:
    matches_type: IsSubclassMCS

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.matches_type = match_type(cls)
