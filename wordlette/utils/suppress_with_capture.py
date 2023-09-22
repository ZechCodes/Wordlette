class SuppressWithCapture:
    def __init__(self, *exceptions):
        self._exceptions = exceptions
        self._captured = None

    @property
    def captured(self) -> Exception | None:
        return self._captured

    def __bool__(self) -> bool:
        return self._captured is not None

    def __iter__(self):
        yield self._captured

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._captured = exc_value
        return exc_type is not None and issubclass(exc_type, self._exceptions)
