from typing import Type, cast


class Sentinel:
    def __new__(cls):
        inst = super().__new__(cls)
        cls.__new__ = lambda _: inst
        return inst

    def __repr__(self):
        return f"<{type(self).__name__}>"


def sentinel(name: str) -> tuple[Type[Sentinel], Sentinel]:
    """Create a new sentinel type."""

    cls = cast(Type[Sentinel], type(name, (Sentinel,), {}))
    return cls, cls()
