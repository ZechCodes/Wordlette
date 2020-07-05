import bevy
import toml
import wordlette.logging
import wordlette.path
from typing import Any, Dict, Optional


class Config(bevy.Bevy):
    path: wordlette.path.Path
    log: wordlette.logging.Logging

    def __init__(self):
        self._files = {}

    def get(self, name: str, default: Optional[Any] = None, /, *, require: bool = False) -> Dict[str, Any]:
        path = self.path.build_path(name, extension="toml")
        if not path.exists():
            if require:
                raise FileExistsError(
                    f"Unable to find a config file with the name '{name}'\n- Checked {path.resolve()}"
                )
            self.log.debug(f"Config file {path.resolve()} does not exist, falling back to default value")
            return default

        self.log.debug(f"Config file {path.resolve()} exists")
        return toml.load(path)

