from typing import Any


class DatabaseStatus:
    def __eq__(self, other):
        if not isinstance(other, DatabaseStatus):
            raise NotImplementedError()

        return bool(self) == bool(other)


class DatabaseErrorStatus(DatabaseStatus):
    __match_args__ = ("error",)

    def __init__(self, error: Exception):
        self.error = error

    def __bool__(self):
        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.error!r})"


class DatabaseSuccessStatus(DatabaseStatus):
    __match_args__ = ("result",)

    def __init__(self, result: Any):
        self.result = result

    def __bool__(self):
        return True

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.result!r})"