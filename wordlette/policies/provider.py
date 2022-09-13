from bevy.providers import TypeProvider

from . import Policy


class PolicyProvider(TypeProvider, priority="high"):
    def supports(self, obj) -> bool:
        return isinstance(obj, type) and issubclass(obj, Policy)
