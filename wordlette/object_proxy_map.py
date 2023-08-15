from collections.abc import Mapping


class ObjectProxyMap(Mapping):
    def __init__(self, obj):
        self.data = obj

    def __contains__(self, item):
        if item.startswith("_"):
            return False

        return hasattr(self.data, item)

    def __getitem__(self, item):
        if item not in self:
            raise KeyError(item)

        return getattr(self.data, item)

    def __iter__(self):
        return iter(key for key in dir(self.data) if not key.startswith("_"))

    def __len__(self):
        return sum(1 for _ in self)

    def __repr__(self):
        data = ", ".join(f"{key!r}: {value!r}" for key, value in self.items())
        return f"{{{data}}}"
