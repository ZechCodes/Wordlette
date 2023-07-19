from io import StringIO
from typing import Any, BinaryIO

try:
    import yaml

except ImportError:
    yaml = None

from wordlette.configs.handlers import Serializable, ConfigHandler


class YamlHandler(ConfigHandler):
    extensions = {"yaml", "yml"}

    def load(self, file: BinaryIO) -> dict[str, Any]:
        if not yaml:
            raise ImportError("pyyaml is required to load YAML files.")

        return yaml.safe_load(file)

    def write(self, data: dict | Serializable, file: BinaryIO):
        if not yaml:
            raise ImportError("pyyaml is required to write YAML files.")

        def write(d):
            yaml.safe_dump(d, f := StringIO())
            file.write(f.getvalue().encode())

        match data:
            case dict():
                write(data)

            case Serializable():
                write(data.to_dict())

            case _:
                raise TypeError(
                    f"Cannot write type {type(data)!r} into a YAML file. Must be a dict or adhere to the "
                    f"`{Serializable.__module__}.{Serializable.__qualname__}` protocol."
                )

    @classmethod
    def supported(cls) -> bool:
        return yaml is not None
