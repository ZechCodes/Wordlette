from typing import Any, Protocol, runtime_checkable, BinaryIO


@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]:
        ...


@runtime_checkable
class ConfigHandler(Protocol):
    extensions: set[str]

    def load(self, file: BinaryIO) -> dict[str, Any]:
        ...

    def write(self, data: dict | Serializable, file: BinaryIO):
        ...
