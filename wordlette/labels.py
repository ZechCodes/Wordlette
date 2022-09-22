from typing import Generator, Generic, TypeVar


T = TypeVar("T")


class Label(Generic[T]):
    def __init__(self, *values, **labels):
        self.labels = set(labels.items())
        self.values: set[T] = set(values)

    def matches(self, **labels) -> bool:
        return self.labels.issubset(labels.items())

    def exact_match(self, **labels) -> bool:
        return len(self.labels.difference(labels.items())) == 0


class LabelCollection(Generic[T]):
    def __init__(self):
        self.labels: set[Label[T]] = set()

    def get(self, **labels) -> Generator[None, T, None]:
        for label in self.labels:
            if label.matches(**labels):
                yield from label.values

    def add(self, *values: T, **labels):
        for label in self.labels:
            if label.exact_match(**labels):
                label.values.update(values)
                return

        self.labels.add(Label(*values, **labels))
