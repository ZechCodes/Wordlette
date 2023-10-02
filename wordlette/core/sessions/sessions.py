from typing import Mapping, Any


class Session(Mapping):
    def __init__(self, session_id: str, session: dict[str, Any]):
        self._session_id = session_id
        self._session = session
        self._overwrites = {}
        self._deletes = set()

    @property
    def num_additions(self) -> int:
        return len(self._overwrites)

    @property
    def num_deletions(self) -> int:
        return len(self._deletes)

    @property
    def num_changes(self) -> int:
        return self.num_additions + self.num_deletions

    @property
    def session_id(self) -> str:
        return self._session_id

    def flatten(self) -> dict[str, Any]:
        return dict(self.items())

    def keys(self):
        keys = set(self._session.keys())
        keys |= set(self._overwrites.keys())
        keys -= self._deletes
        return keys

    def __getitem__(self, key: str) -> Any:
        if key in self._overwrites:
            return self._overwrites[key]

        if key not in self._deletes and key in self._session:
            return self._session[key]

        raise KeyError(key)

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def __setitem__(self, key: str, value: Any):
        self._overwrites[key] = value
        self._deletes.discard(key)

    def __delitem__(self, key: str):
        del self._overwrites[key]
        self._deletes.add(key)

    def __repr__(self):
        return f"Session({self.session_id!r}, {self._overwrites})"
