from typing import _AnnotatedAlias


class AnnotatedAggregator(_AnnotatedAlias, _root=True):
    def __ror__(self, other):
        self.__origin__ = other | self.__origin__
        return self

    def __class_getitem__(cls, item):
        origin, *args = item
        if origin is None:
            origin = type(None)

        return cls(origin, tuple(args))
