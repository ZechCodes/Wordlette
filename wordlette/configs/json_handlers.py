import json
from io import StringIO
from typing import Any, BinaryIO

from wordlette.configs.handlers import Serializable, ConfigHandler


class JsonHandler(ConfigHandler):
    extensions = {"json"}

    def load(self, file: BinaryIO) -> dict[str, Any]:
        return json.load(file)

    def write(self, data: dict | Serializable, file: BinaryIO):
        def write(d):
            json.dump(d, f := StringIO(), indent=2)
            file.write(f.getvalue().encode())

        match data:
            case dict():
                write(data)

            case Serializable():
                write(data.to_dict())

            case _:
                raise TypeError(
                    f"Cannot write type {type(data)!r} into a JSON file. Must be a dict or adhere to the "
                    f"`{Serializable.__module__}.{Serializable.__qualname__}` protocol."
                )
