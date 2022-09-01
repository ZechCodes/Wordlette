from bevy import Bevy
from typing import Iterator

from wordlette.extensions.plugins import Plugin


class Extension(Bevy):
    def __init__(self, name: str):
        self.name = name
        self.plugins = set()

    def load_plugins(self, plugins: Iterator[Plugin]):
        for constructor in plugins:
            plugin = self.bevy.create(constructor, cache=True)
            self.plugins.add(plugin)

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r}, plugins={self.plugins})"


class AppExtension(Extension):
    ...
