from typing import BinaryIO, Any

from wordlette.configs.exceptions import (
    ConfigCannotCreateFiles,
    ConfigCannotLoadFiles,
)

try:
    import tomlkit as toml

    can_write = True
except ImportError:
    can_write = False

    try:
        import tomllib as toml
    except ImportError:
        toml = None

from wordlette.configs.handlers import Serializable, ConfigHandler


class TomlHandler(ConfigHandler):
    extensions = {"toml"}

    def load(self, file: BinaryIO) -> dict[str, Any]:
        if not toml:
            raise ConfigCannotLoadFiles(
                "You must install tomlkit or tomllib to load TOML files."
            )

        return toml.load(file)

    def write(self, data: dict | Serializable, file: BinaryIO):
        if not can_write:
            raise ConfigCannotCreateFiles(
                "You must install tomlkit to write TOML files."
            )

        def write(d):
            file.write(toml.dumps(d).encode())

        match data:
            case dict():
                write(data)

            case Serializable():
                write(data.to_dict())

            case _:
                raise TypeError(
                    f"Cannot write type {type(data)!r} into a TOML file. Must be a dict or adhere to the "
                    f"`{Serializable.__module__}.{Serializable.__qualname__}` protocol."
                )

    @classmethod
    def supported(cls) -> bool:
        return toml is not None
